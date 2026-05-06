"""Repetition scoring for summarized ChatDev interactions.

This module scores FM-1.3 style step repetition without calling an LLM or
embedding API.  It is designed for classified summarized datasets where each
interaction contains a list of atomic ``output`` items.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_WINDOW = 3
WORD_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass
class RepetitionMatch:
    """Best previous-output match for one output item."""

    score: float
    reference_index: int
    reference_turn: Optional[int]
    reference_phase: str
    reference_output: str
    exact_match: bool
    sequence_similarity: float
    token_jaccard: float

    def to_dict(self, output: str) -> Dict[str, Any]:
        return {
            "output": output,
            "score": self.score,
            "reference_index": self.reference_index,
            "reference_turn": self.reference_turn,
            "reference_phase": self.reference_phase,
            "reference_output": self.reference_output,
            "exact_match": self.exact_match,
            "sequence_similarity": self.sequence_similarity,
            "token_jaccard": self.token_jaccard,
        }


def score_summarized_json(
    input_path: str | Path,
    output_path: str | Path | None = None,
    window: int = DEFAULT_WINDOW,
) -> Dict[str, Any]:
    """Load a summarized JSON file, add repetition scores, and optionally write it."""
    input_path = Path(input_path)
    with input_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    scored = score_summarized_data(data, window=window)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(scored, file, ensure_ascii=False, indent=2)

    return scored


def score_summarized_data(data: Dict[str, Any], window: int = DEFAULT_WINDOW) -> Dict[str, Any]:
    """Return a scored copy of one role-grouped summarized playbook."""
    result: Dict[str, Any] = {}
    for role, interactions in data.items():
        if not isinstance(interactions, list):
            result[role] = copy.deepcopy(interactions)
            continue

        history: List[Dict[str, Any]] = []
        scored_interactions = []
        for entry in interactions:
            if not isinstance(entry, dict):
                scored_interactions.append(copy.deepcopy(entry))
                continue

            scored_entry = score_entry(entry, history=history, window=window)
            scored_interactions.append(scored_entry)
            for output_item in _as_output_items(entry.get("output")):
                if output_item.strip():
                    history.append(
                        {
                            "output": output_item,
                            "turn": entry.get("turn"),
                            "phase": entry.get("phase") or "",
                        }
                    )
        result[role] = scored_interactions
    return result


def score_entry(
    entry: Dict[str, Any],
    history: Sequence[Dict[str, Any]],
    window: int = DEFAULT_WINDOW,
) -> Dict[str, Any]:
    """Return a copy of one interaction with FM-1.3 repetition scores appended."""
    scored = copy.deepcopy(entry)
    output_items = _as_output_items(scored.get("output"))
    recent_history = list(history[-max(0, window) :]) if window else list(history)

    item_scores = []
    for output_item in output_items:
        match = best_repetition_match(output_item, recent_history)
        item_scores.append(match.to_dict(output_item))

    repetition_scores = [float(item["score"]) for item in item_scores]
    repetition_mean = mean(repetition_scores) if repetition_scores else 0.0
    repetition_max = max(repetition_scores) if repetition_scores else 0.0
    repetition_min = min(repetition_scores) if repetition_scores else 0.0

    scored["repetition_scoring_context"] = {
        "failure_mode": "1.3 Step Repetition",
        "window": window,
        "scope": "same role, previous output items",
        "score_range": "0 means novel, 1 means exact or near-identical repetition",
        "formula": "max(exact_match, 0.65 * SequenceMatcher + 0.35 * token_jaccard)",
    }
    scored["output_repetition_scores"] = item_scores
    scored["repetition_score_mean__fm_1_3"] = round(float(repetition_mean), 4)
    scored["repetition_score_max__fm_1_3"] = round(float(repetition_max), 4)
    scored["repetition_score_min__fm_1_3"] = round(float(repetition_min), 4)

    # Keep compatibility with the existing visualization pipeline, which treats
    # consistency scores as higher-is-better.  Here, "consistency" is novelty.
    scored["consistency_score_mean"] = round(float(1.0 - repetition_mean), 4)
    scored["consistency_score_min"] = round(float(1.0 - repetition_max), 4)
    scored["consistency_score_max"] = round(float(1.0 - repetition_min), 4)
    return scored


def best_repetition_match(output: str, history: Sequence[Dict[str, Any]]) -> RepetitionMatch:
    """Return the strongest repetition match against historical outputs."""
    if not output or not str(output).strip() or not history:
        return RepetitionMatch(0.0, -1, None, "", "", False, 0.0, 0.0)

    best: Tuple[float, int, Dict[str, Any], bool, float, float] = (
        0.0,
        -1,
        {},
        False,
        0.0,
        0.0,
    )
    for index, item in enumerate(history):
        previous = str(item.get("output") or "")
        exact, sequence, jaccard, score = repetition_similarity(output, previous)
        if score > best[0]:
            best = (score, index, item, exact, sequence, jaccard)

    score, index, item, exact, sequence, jaccard = best
    return RepetitionMatch(
        score=round(float(score), 4),
        reference_index=index,
        reference_turn=item.get("turn"),
        reference_phase=str(item.get("phase") or ""),
        reference_output=str(item.get("output") or ""),
        exact_match=exact,
        sequence_similarity=round(float(sequence), 4),
        token_jaccard=round(float(jaccard), 4),
    )


def repetition_similarity(left: str, right: str) -> Tuple[bool, float, float, float]:
    """Return exact flag, character similarity, token Jaccard, and final score."""
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if not left_norm or not right_norm:
        return False, 0.0, 0.0, 0.0

    exact = left_norm == right_norm
    sequence = SequenceMatcher(None, left_norm, right_norm).ratio()
    left_tokens = set(tokenize(left_norm))
    right_tokens = set(tokenize(right_norm))
    if left_tokens or right_tokens:
        jaccard = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    else:
        jaccard = 0.0
    score = 1.0 if exact else 0.65 * sequence + 0.35 * jaccard
    return exact, sequence, jaccard, max(0.0, min(1.0, score))


def normalize_text(text: str) -> str:
    """Normalize text for stable lexical repetition matching."""
    text = str(text).lower()
    text = re.sub(r"`+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> List[str]:
    """Tokenize normalized text into word-like units."""
    return WORD_RE.findall(text)


def _as_output_items(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []

