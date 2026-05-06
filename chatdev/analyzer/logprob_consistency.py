"""
Logprob-based consistency scoring for summarized ChatDev interactions.

This module implements the strict binary LLM-as-a-judge pattern described in
``CLAUDE_TODO/TODO.md``.  Each output item is judged against the initial user
task, the interaction's known context, and the task list by forcing the model to
choose one token:
``Yes`` or ``No``.  The final score is the summed probability mass of positive
tokens in the returned top logprobs.
"""

import copy
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from openai import OpenAI


DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TOP_LOGPROBS = 5
DEFAULT_PREMISE_ORDER = ("user_demand", "known_context", "tasks")
VALID_PREMISE_KEYS = set(DEFAULT_PREMISE_ORDER)
POSITIVE_TOKENS = {"yes", " yes", "y", " y", "yes.", " true", "true"}
USER_TASK_KEYS = ("user_demand", "user_task", "task_prompt", "initial_task", "initial_user_task")
CHATDEV_FILENAME_PATTERN = re.compile(
    r"^ChatDev_(ProgramDev2?|ProgramDev)_GPT4o_(\d+)_(?:playbook|summarized|scored)\.json$"
)


def _load_env() -> None:
    """Load a local .env file when python-dotenv is available."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    current = os.getcwd()
    while True:
        env_path = os.path.join(current, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            return
        parent = os.path.dirname(current)
        if parent == current:
            return
        current = parent


def _default_client() -> OpenAI:
    _load_env()
    base_url = os.environ.get("BASE_URL") or os.environ.get("OPENAI_BASE_URL")
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url=base_url)


@dataclass
class ConsistencyResult:
    """One binary-judge result for a single hypothesis/output item."""

    score: float
    generated_token: str
    generated_token_logprob: Optional[float]
    generated_token_probability: Optional[float]
    positive_probability: float
    negative_probability: float
    top_logprobs: List[Dict[str, float]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": float(self.score),
            "generated_token": self.generated_token,
            "generated_token_logprob": self.generated_token_logprob,
            "generated_token_probability": self.generated_token_probability,
            "positive_probability": float(self.positive_probability),
            "negative_probability": float(self.negative_probability),
            "top_logprobs": [
                {
                    "token": item["token"],
                    "logprob": item["logprob"],
                    "probability": item["probability"],
                }
                for item in self.top_logprobs
            ],
        }


class LogprobConsistencyScorer:
    """Score atomic output items against atomic premises using logprobs.

    Args:
        client: OpenAI-compatible client. A custom client can be injected in
            tests or when using a compatible endpoint.
        model: Judge model. Defaults to ``gpt-4o-mini``.
        top_logprobs: Number of candidate token logprobs to request.
        positive_tokens: Tokens treated as positive/Yes answers.
    """

    def __init__(
        self,
        client: Optional[Any] = None,
        model: str = DEFAULT_MODEL,
        top_logprobs: int = DEFAULT_TOP_LOGPROBS,
        positive_tokens: Optional[Iterable[str]] = None,
        negative_tokens: Optional[Iterable[str]] = None,
        premise_order: Optional[Sequence[str]] = None,
    ) -> None:
        self.client = client or _default_client()
        self.model = model
        self.top_logprobs = top_logprobs
        self.premise_order = normalize_premise_order(premise_order)
        self.positive_tokens = {
            token.lower() for token in (positive_tokens or POSITIVE_TOKENS)
        }
        self.negative_tokens = {
            token.lower()
            for token in (negative_tokens or {"no", " no", "n", " n", "no.", " false", "false"})
        }
        self._stats = {"api_calls": 0, "scored_outputs": 0, "errors": 0}

    def score(self, premises: Sequence[str], hypothesis: str) -> ConsistencyResult:
        """Return the logprob consistency score for one hypothesis."""
        if not hypothesis or not hypothesis.strip():
            return ConsistencyResult(0.0, "", None, None, 0.0, 0.0, [])

        prompt = build_binary_prompt(premises, hypothesis)
        self._stats["api_calls"] += 1

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1,
                temperature=0.0,
                logprobs=True,
                top_logprobs=self.top_logprobs,
            )
            result = self._parse_response(response)
            self._stats["scored_outputs"] += 1
            return result
        except Exception as exc:
            self._stats["errors"] += 1
            raise RuntimeError(f"Logprob consistency scoring failed: {exc}") from exc

    def score_entry(
        self,
        entry: Dict[str, Any],
        user_task: Optional[str] = None,
        premise_order: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        """Return a copy of one summarized interaction with scores appended."""
        scored = copy.deepcopy(entry)
        entry_user_task = _extract_user_task_from_mapping(scored)
        effective_user_task = user_task or entry_user_task
        selected_premise_order = normalize_premise_order(premise_order or self.premise_order)
        premises = build_premises(
            scored,
            user_task=effective_user_task,
            premise_order=selected_premise_order,
        )
        output_items = scored.get("output") or []

        item_scores: List[Dict[str, Any]] = []
        for output_item in output_items:
            result = self.score(premises, str(output_item))
            item_scores.append(
                {
                    "output": output_item,
                    **result.to_dict(),
                }
            )

        if effective_user_task:
            scored["user_demand"] = effective_user_task
            scored["scoring_context"] = {
                "user_demand_in_prompt": "user_demand" in selected_premise_order,
                "premise_order": list(selected_premise_order),
                "available_premise_order": list(DEFAULT_PREMISE_ORDER),
                "judge_rule": (
                    "Yes iff at least one premise supports the output and no "
                    "premise contradicts it; No if any premise contradicts it "
                    "or if no premise supports it."
                ),
            }
        scored["output_consistency_scores"] = item_scores
        aggregates = aggregate_scores([item["score"] for item in item_scores])
        scored.update(aggregates)
        return scored

    def score_summarized_data(
        self,
        data: Dict[str, Any],
        user_task: Optional[str] = None,
        premise_order: Optional[Sequence[str]] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Score a summarized JSON object grouped by role."""
        effective_user_task = user_task
        selected_premise_order = normalize_premise_order(premise_order or self.premise_order)
        result: Dict[str, Any] = {}
        for role, interactions in data.items():
            if not isinstance(interactions, list):
                result[role] = copy.deepcopy(interactions)
                continue

            role_entries = []
            for index, entry in enumerate(interactions, start=1):
                if not isinstance(entry, dict):
                    role_entries.append(copy.deepcopy(entry))
                    continue
                role_entries.append(
                    self.score_entry(
                        entry,
                        user_task=effective_user_task,
                        premise_order=selected_premise_order,
                    )
                )
                if verbose:
                    print(f"[{role}] scored {index}/{len(interactions)}")
            result[role] = role_entries
        return result

    def score_summarized_json(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        user_task: Optional[str] = None,
        user_task_map: Optional[Dict[str, str]] = None,
        dataset_path: Optional[str] = None,
        trajectory_dir: Optional[str] = None,
        premise_order: Optional[Sequence[str]] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Load summarized JSON, append scores, optionally write a new file."""
        with open(input_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        effective_user_task = user_task or infer_user_task_for_path(
            input_path,
            user_task_map=user_task_map,
            dataset_path=dataset_path,
            trajectory_dir=trajectory_dir,
        )

        scored = self.score_summarized_data(
            data,
            user_task=effective_user_task,
            premise_order=premise_order,
            verbose=verbose,
        )

        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as file:
                json.dump(scored, file, ensure_ascii=False, indent=2)

        return scored

    def _parse_response(self, response: Any) -> ConsistencyResult:
        choice = response.choices[0]
        token_data = choice.logprobs.content[0]
        generated_token = getattr(token_data, "token", "") or ""
        generated_token_logprob = _get_optional_float(token_data, "logprob")
        generated_token_probability = (
            _safe_exp(generated_token_logprob)
            if generated_token_logprob is not None
            else None
        )
        top_logprobs = [_candidate_to_dict(cand) for cand in (token_data.top_logprobs or [])]

        # Some OpenAI-compatible gateways omit the selected token from
        # top_logprobs.  Keep the generated token in the probability table so
        # downstream JSON always explains the final model choice.
        if generated_token and generated_token_logprob is not None:
            normalized_generated = generated_token.lower()
            has_generated_token = any(
                candidate["token"].lower() == normalized_generated
                for candidate in top_logprobs
            )
            if not has_generated_token:
                top_logprobs.insert(
                    0,
                    {
                        "token": generated_token,
                        "logprob": generated_token_logprob,
                        "probability": generated_token_probability,
                    },
                )

        positive_probability = 0.0
        negative_probability = 0.0
        for candidate in top_logprobs:
            if candidate["token"].lower() in self.positive_tokens:
                positive_probability += candidate["probability"]
            if candidate["token"].lower() in self.negative_tokens:
                negative_probability += candidate["probability"]

        positive_probability = _clamp_probability(positive_probability)
        negative_probability = _clamp_probability(negative_probability)
        score = max(0.0, min(1.0, positive_probability))
        return ConsistencyResult(
            score=score,
            generated_token=generated_token,
            generated_token_logprob=generated_token_logprob,
            generated_token_probability=generated_token_probability,
            positive_probability=positive_probability,
            negative_probability=negative_probability,
            top_logprobs=top_logprobs,
        )

    @property
    def stats(self) -> Dict[str, int]:
        return dict(self._stats)


def build_binary_prompt(premises: Sequence[str], hypothesis: str) -> str:
    premises_text = "\n".join(
        f"P{i}. {item}"
        for i, item in enumerate(premises, start=1)
        if str(item).strip()
    )
    return f"""You are a strict binary consistency judge.

Your task is to decide whether the OUTPUT is acceptable under the PREMISES.

Decision rule:
1. Answer "Yes" if at least one premise directly or reasonably supports the OUTPUT, and no premise contradicts the OUTPUT.
2. Answer "Yes" when one premise supports the OUTPUT and the remaining premises are unrelated or silent.
3. Answer "No" if any premise contradicts the OUTPUT, even when multiple other premises support it.
4. Answer "No" if no premise supports the OUTPUT.
5. Treat "contradicts" as violating, reversing, replacing, or adding behavior that is incompatible with a premise.
6. Do not require every premise to support the OUTPUT. Unrelated premises are neutral.

Examples:
Premises:
P1. The user requested a command-line tool.
P2. The tool should count words in a text file.
Output:
Implemented a CLI argument parser.
Answer:
Yes

Premises:
P1. The user requested a command-line tool.
P2. The tool should count words in a text file.
Output:
Implemented a graphical desktop interface as the main interaction mode.
Answer:
No

Premises:
P1. The app should export CSV files.
P2. The app should validate input file paths.
Output:
Added input path validation.
Answer:
Yes

Premises:
P1. The app should export CSV files.
P2. The app must not use a database.
P3. The app should validate input file paths.
Output:
Added input path validation and stored all records in SQLite.
Answer:
No

Output exactly one word: "Yes" or "No".
Do not output punctuation, explanations, or extra text.

PREMISES:
{premises_text}

OUTPUT:
{hypothesis}

Answer:"""


def build_premises(
    entry: Dict[str, Any],
    user_task: Optional[str] = None,
    premise_order: Optional[Sequence[str]] = None,
) -> List[str]:
    """Build judge premises in the selected order.

    By default the initial user task is first, followed by role-local context
    and tasks.  Callers can pass a subset such as ``["tasks"]`` to score only
    against that premise group.
    """
    selected_premise_order = normalize_premise_order(premise_order)
    premises: List[str] = []
    for premise_key in selected_premise_order:
        if premise_key == "user_demand":
            if user_task:
                premises.append(f"Initial user task: {user_task}")
        elif premise_key == "known_context":
            premises.extend(str(item) for item in (entry.get("known_context") or []))
        elif premise_key == "tasks":
            premises.extend(str(item) for item in (entry.get("tasks") or []))
    return premises


def normalize_premise_order(premise_order: Optional[Sequence[str]] = None) -> tuple:
    """Validate and normalize selected premise keys.

    Valid keys are ``user_demand``, ``known_context``, and ``tasks``.  Passing a
    subset scores outputs only against those premise groups while preserving the
    caller-provided order.
    """
    if premise_order is None:
        return DEFAULT_PREMISE_ORDER

    normalized = tuple(str(item).strip() for item in premise_order if str(item).strip())
    if not normalized:
        raise ValueError("premise_order must include at least one premise key")

    invalid = [item for item in normalized if item not in VALID_PREMISE_KEYS]
    if invalid:
        raise ValueError(
            "Invalid premise_order key(s): "
            f"{invalid}. Expected a subset of {list(DEFAULT_PREMISE_ORDER)}."
        )

    duplicates = [item for index, item in enumerate(normalized) if item in normalized[:index]]
    if duplicates:
        raise ValueError(f"premise_order contains duplicate key(s): {duplicates}")

    return normalized


def load_user_task_map(
    dataset_path: str = "chatdev_dataset.json",
    trajectory_dir: str = "data/classified_chatdev_playbook/trajectory",
) -> Dict[str, str]:
    """Load ``filename -> user_demand`` from chatdev_dataset.json.

    The project dataset is aligned by order: the Nth item in
    ``chatdev_dataset.json`` corresponds to the Nth playbook filename after
    sorting the files in the trajectory directory.
    """
    dataset = Path(dataset_path)
    trajectory = Path(trajectory_dir)
    if not dataset.is_absolute():
        root = _find_project_root()
        dataset = root / dataset
    if not trajectory.is_absolute():
        root = _find_project_root()
        trajectory = root / trajectory

    with dataset.open("r", encoding="utf-8") as file:
        records = json.load(file)
    trajectory_files = sorted(
        (path for path in trajectory.glob("*.json") if path.is_file()),
        key=lambda path: chatdev_filename_sort_key(path.name),
    )

    if len(records) != len(trajectory_files):
        raise ValueError(
            "chatdev_dataset.json length does not match trajectory file count: "
            f"{len(records)} != {len(trajectory_files)}"
        )

    mapping: Dict[str, str] = {}
    for record, playbook_path in zip(records, trajectory_files):
        user_demand = str(record.get("user_demand", "") or "").strip()
        playbook_name = playbook_path.name
        summarized_name = _playbook_name_to_summarized_name(playbook_name)
        scored_name = _summarized_name_to_scored_name(summarized_name)
        mapping[playbook_name] = user_demand
        mapping[summarized_name] = user_demand
        mapping[scored_name] = user_demand
    return mapping


def infer_user_task_for_path(
    path: str,
    user_task_map: Optional[Dict[str, str]] = None,
    dataset_path: Optional[str] = None,
    trajectory_dir: Optional[str] = None,
) -> Optional[str]:
    """Infer a user task from a summarized/playbook filename."""
    mapping = user_task_map
    if mapping is None:
        try:
            mapping = load_user_task_map(
                dataset_path=dataset_path or "chatdev_dataset.json",
                trajectory_dir=trajectory_dir or "data/classified_chatdev_playbook/trajectory",
            )
        except Exception:
            return None

    name = Path(path).name
    if name in mapping:
        return mapping[name]
    for alternate in _candidate_dataset_names(name):
        if alternate in mapping:
            return mapping[alternate]
    return None


def aggregate_scores(scores: Sequence[float]) -> Dict[str, Optional[float]]:
    if not scores:
        return {
            "consistency_score_mean": None,
            "consistency_score_min": None,
            "consistency_score_max": None,
        }
    values = [float(score) for score in scores]
    return {
        "consistency_score_mean": sum(values) / len(values),
        "consistency_score_min": min(values),
        "consistency_score_max": max(values),
    }


def _candidate_to_dict(candidate: Any) -> Dict[str, float]:
    if isinstance(candidate, dict):
        logprob = float(candidate.get("logprob", float("-inf")))
        return {
            "token": str(candidate.get("token", "")),
            "logprob": logprob,
            "probability": _safe_exp(logprob),
        }
    logprob = float(getattr(candidate, "logprob", float("-inf")))
    return {
        "token": str(getattr(candidate, "token", "")),
        "logprob": logprob,
        "probability": _safe_exp(logprob),
    }


def _get_optional_float(obj: Any, name: str) -> Optional[float]:
    if isinstance(obj, dict):
        value = obj.get(name)
    else:
        value = getattr(obj, name, None)
    if value is None:
        return None
    return float(value)


def _safe_exp(logprob: float) -> float:
    if math.isinf(logprob) and logprob < 0:
        return 0.0
    return math.exp(logprob)


def _clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, value))


def _extract_user_task_from_summarized_data(data: Dict[str, Any]) -> Optional[str]:
    direct = _extract_user_task_from_mapping(data)
    if direct:
        return direct

    metadata = data.get("metadata") or data.get("_metadata")
    if isinstance(metadata, dict):
        metadata_task = _extract_user_task_from_mapping(metadata)
        if metadata_task:
            return metadata_task

    for interactions in data.values():
        if not isinstance(interactions, list):
            continue
        for entry in interactions:
            if isinstance(entry, dict):
                entry_task = _extract_user_task_from_mapping(entry)
                if entry_task:
                    return entry_task
    return None


def _extract_user_task_from_mapping(mapping: Dict[str, Any]) -> Optional[str]:
    for key in USER_TASK_KEYS:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _playbook_name_to_summarized_name(name: str) -> str:
    if name.endswith("_playbook.json"):
        return name[: -len("_playbook.json")] + "_summarized.json"
    return name


def _summarized_name_to_playbook_name(name: str) -> str:
    if name.endswith("_summarized.json"):
        return name[: -len("_summarized.json")] + "_playbook.json"
    return name


def _scored_name_to_playbook_name(name: str) -> str:
    if name.endswith("_scored.json"):
        return name[: -len("_scored.json")] + "_playbook.json"
    return name


def _scored_name_to_summarized_name(name: str) -> str:
    if name.endswith("_scored.json"):
        return name[: -len("_scored.json")] + "_summarized.json"
    return name


def _summarized_name_to_scored_name(name: str) -> str:
    if name.endswith("_summarized.json"):
        return name[: -len("_summarized.json")] + "_scored.json"
    return name


def _candidate_dataset_names(name: str) -> List[str]:
    return [
        _summarized_name_to_playbook_name(name),
        _scored_name_to_playbook_name(name),
        _scored_name_to_summarized_name(name),
    ]


def chatdev_filename_sort_key(name: str) -> tuple:
    """Sort ChatDev files in dataset alignment order.

    ``chatdev_dataset.json`` is aligned to trajectory files with the original
    ProgramDev batch first, then ProgramDev2, and numeric order within each
    batch. Plain lexicographic sorting is wrong because ``ProgramDev2`` sorts
    before ``ProgramDev_``.
    """
    match = CHATDEV_FILENAME_PATTERN.match(name)
    if not match:
        return (99, name)
    family, number = match.groups()
    family_rank = 0 if family == "ProgramDev" else 1
    return (family_rank, int(number), name)


def _find_project_root() -> Path:
    current = Path.cwd()
    for candidate in [current, *current.parents]:
        if (candidate / "chatdev_dataset.json").exists():
            return candidate
    return current


_default_scorer: Optional[LogprobConsistencyScorer] = None


def _get_default_scorer() -> LogprobConsistencyScorer:
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = LogprobConsistencyScorer()
    return _default_scorer


def evaluate_consistency_with_logprobs(premises: Sequence[str], hypothesis: str) -> float:
    """Convenience function returning only the positive-token probability."""
    return _get_default_scorer().score(premises, hypothesis).score


def score_summarized_json(
    input_path: str,
    output_path: Optional[str] = None,
    user_task: Optional[str] = None,
    user_task_map: Optional[Dict[str, str]] = None,
    dataset_path: Optional[str] = None,
    trajectory_dir: Optional[str] = None,
    premise_order: Optional[Sequence[str]] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Convenience function for scoring a summarized JSON file."""
    return _get_default_scorer().score_summarized_json(
        input_path=input_path,
        output_path=output_path,
        user_task=user_task,
        user_task_map=user_task_map,
        dataset_path=dataset_path,
        trajectory_dir=trajectory_dir,
        premise_order=premise_order,
        verbose=verbose,
    )
