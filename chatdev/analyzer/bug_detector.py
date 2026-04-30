"""
bug_detector.py - Two-Step Bug Detection Module

Implements the TODO.md design philosophy:
  Step 1 (LLM Brain):  ClaimExtractor — extracts "Atomic Claims" from unstructured agent output,
                        stripping social chatter and emotional expressions.
  Step 2 (Algorithmic Judge): ClaimScorer — computes evaluation scores per claim using
                        embedding-based similarity and anchor-point deviation.

Architecture:
  ClaimExtractor  →  produces List[Claim] from raw agent output
  ClaimScorer     →  scores each claim against constraints & context
  BugDetector     →  orchestrates the pipeline over a playbook, returns ScoredPlaybook

All scorers produce scores in human-readable ranges (typically 0–1 or -1–1).
No error classification is done — that is reserved for a future layer (ErrorLocator, ErrorClassifier).
"""

import os
import json
import numpy as np
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field


# ============================================================================
#  Environment & OpenAI client initialization
# ============================================================================

def _load_env():
    search_dirs = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__))
    ]

    possible_paths = []
    for start_dir in search_dirs:
        curr = start_dir
        while True:
            p = os.path.join(curr, '.env')
            if os.path.exists(p):
                if p not in possible_paths:
                    possible_paths.append(p)
                break
            parent = os.path.dirname(curr)
            if parent == curr:
                break
            curr = parent

    loaded_path = None
    try:
        from dotenv import load_dotenv
        for p in possible_paths:
            load_dotenv(p, override=True)
            loaded_path = p
            break
    except ImportError:
        pass

    if not loaded_path:
        for p in possible_paths:
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            parts = line.strip().split('=', 1)
                            if len(parts) == 2:
                                k, v = parts
                                os.environ[k.strip()] = v.strip()
                loaded_path = p
                break
            except Exception:
                continue

_load_env()

from openai import OpenAI

effective_base_url = os.environ.get("BASE_URL") or os.environ.get("OPENAI_BASE_URL")

_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=effective_base_url
)


# ============================================================================
#  Embedding utilities
# ============================================================================

_EMBEDDING_CACHE: Dict[str, np.ndarray] = {}

def get_embeddings_batch(texts: List[str], model: str = "text-embedding-3-small") -> List[np.ndarray]:
    """Fetch embeddings for a list of texts with batching and caching."""
    if not texts:
        return []

    results = []
    to_fetch = []
    for t in texts:
        t_clean = t.replace("\n", " ").strip()
        if not t_clean:
            results.append(np.zeros(1536))
            continue
        if t_clean in _EMBEDDING_CACHE:
            results.append(_EMBEDDING_CACHE[t_clean])
        else:
            to_fetch.append(t_clean)
            results.append(None)

    if to_fetch:
        chunk_size = 500
        fetched_embs = []
        for i in range(0, len(to_fetch), chunk_size):
            chunk = to_fetch[i : i + chunk_size]
            resp = _client.embeddings.create(input=chunk, model=model)
            fetched_embs.extend([np.array(d.embedding) for d in resp.data])

        fetch_idx = 0
        for i, val in enumerate(results):
            if val is None:
                emb = fetched_embs[fetch_idx]
                results[i] = emb
                _EMBEDDING_CACHE[to_fetch[fetch_idx]] = emb
                fetch_idx += 1

        if len(_EMBEDDING_CACHE) > 15000:
            keys_to_delete = list(_EMBEDDING_CACHE.keys())[:5000]
            for k in keys_to_delete:
                del _EMBEDDING_CACHE[k]

    return results


def get_embedding(text: str, model: str = "text-embedding-3-small") -> np.ndarray:
    """Fetch the embedding for a single text."""
    return get_embeddings_batch([text], model=model)[0]


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    return float(dot_product / (norm_vec1 * norm_vec2))


# ============================================================================
#  Data classes for structured results
# ============================================================================

@dataclass
class Claim:
    """An atomic claim extracted from agent output."""
    claim_id: int
    action: str


@dataclass
class NormScoreDetail:
    """Norm compliance score for a single rule."""
    rule: str
    pass_score: float
    fail_score: float
    score: float  # pass_score - fail_score; positive = compliant


@dataclass
class SupportScoreDetail:
    """Support/groundedness score for a single claim."""
    claim_id: int
    claim_text: str
    best_support_context: str
    grounded_score: float  # 0–1, higher = better grounded


@dataclass
class InteractionScores:
    """All evaluation scores for a single interaction (one playbook turn)."""
    role: str
    playbook_turn: int
    phase: str
    phase_turn: int
    node_index: int = -1

    # Extracted claims
    claims: List[Claim] = field(default_factory=list)
    num_claims: int = 0

    # Support / Groundedness scores (FM-2.2, FM-2.3) — 0–1, higher = better
    support_score_details: List[SupportScoreDetail] = field(default_factory=list)
    aggregate_support_score: float = 0.5

    # Norm compliance scores (FM-1.1, FM-1.2) — -1 to 1, positive = compliant
    norm_score_details: List[NormScoreDetail] = field(default_factory=list)
    aggregate_norm_score: float = 0.5

    # Repetition score (FM-1.3) — 0–1, higher = more repetitive (worse)
    repetition_score: float = 0.0
    repetition_reference_turn: int = -1

    # Plan-Action alignment score (FM-2.6) — 0–1, higher = better aligned
    plan_action_alignment_score: float = 0.5
    plan_steps: List[str] = field(default_factory=list)
    action_descriptions: List[str] = field(default_factory=list)

    # Overall health — 0–1 composite, higher = healthier
    overall_health_score: float = 0.5

    # Raw data for traceability
    prompt_snippet: str = ""
    output_snippet: str = ""


@dataclass
class ScoredPlaybook:
    """Complete scored playbook with per-interaction scores and summary statistics."""
    source_playbook_path: str
    source_api_records_path: str = ""
    interactions: List[InteractionScores] = field(default_factory=list)

    num_interactions: int = 0
    num_roles: int = 0
    roles: List[str] = field(default_factory=list)

    support_score_mean: float = 0.0
    support_score_min: float = 0.0
    norm_score_mean: float = 0.0
    norm_score_min: float = 0.0
    repetition_score_mean: float = 0.0
    repetition_score_max: float = 0.0
    plan_action_score_mean: float = 0.0
    plan_action_score_min: float = 0.0
    health_score_mean: float = 0.0
    health_score_min: float = 0.0

    per_role_summary: Dict[str, Dict[str, float]] = field(default_factory=dict)


# ============================================================================
#  Step 1: Claim Extraction — "The LLM Brain"
# ============================================================================

_CLAIM_EXTRACTION_PROMPT = """You are an objective semantic compiler. Read the following text from a multi-agent system output.

Ignore all thanks, pleasantries, emotional expressions, and social chatter.
Extract every substantive operation, API call, business conclusion, code action,
or meaningful decision as an independent "Atomic Claim".

Return strictly a JSON array with no extra text:
[{"claim_id": 1, "action": "the atomic action or decision described"}, ...]

If there are no substantive claims, return an empty array: []"""


class ClaimExtractor:
    """
    Step 1: LLM-based dimension reduction.
    Extracts "Atomic Claims" from unstructured agent output,
    stripping social noise and emotional expressions.
    """

    def __init__(self, client=None, model: str = None):
        self.client = client or _client
        self.model = model or os.environ.get("CLAIM_EXTRACTOR_MODEL", "gpt-4o")

    def extract_claims(self, output_text: str) -> List[Claim]:
        """Extract atomic claims from a single output text via LLM."""
        if not output_text or not output_text.strip():
            return []

        max_chars = 8000
        truncated = output_text if len(output_text) <= max_chars else output_text[:max_chars]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _CLAIM_EXTRACTION_PROMPT},
                    {"role": "user", "content": truncated}
                ],
                temperature=0.0,
            )
            content = response.choices[0].message.content if response.choices else "[]"
        except Exception:
            return extract_claims_fast(output_text)

        return _parse_claim_json(content)

    def extract_claims_batch(self, texts: List[str]) -> List[List[Claim]]:
        """Extract claims from multiple texts."""
        results = []
        for text in texts:
            results.append(self.extract_claims(text))
        return results


def _parse_claim_json(raw_response: str) -> List[Claim]:
    """Parse LLM JSON response into Claim objects."""
    try:
        data = json.loads(raw_response.strip())
        if isinstance(data, list):
            return [Claim(claim_id=c.get("claim_id", i), action=c.get("action", ""))
                    for i, c in enumerate(data)]
    except json.JSONDecodeError:
        pass

    match = re.search(r'\[.*\]', raw_response, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return [Claim(claim_id=c.get("claim_id", i), action=c.get("action", ""))
                        for i, c in enumerate(data)]
        except json.JSONDecodeError:
            pass

    return []


def _remove_code_keep_comments(text: str) -> str:
    """Remove markdown code blocks, retaining comment lines as natural language."""
    lines = text.split('\n')
    in_code_block = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                cleaned = re.sub(r'^(#|//|/\*|\*)\s*', '', stripped)
                if cleaned:
                    if not cleaned.endswith(('.', '!', '?')):
                        cleaned += '.'
                    new_lines.append(cleaned)
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)


def _split_into_sentences(text: str) -> List[str]:
    """Split text into fine-grained sentences by natural language boundaries."""
    text = _remove_code_keep_comments(text)
    text = re.sub(r'(?i)(?:\n\s*(?:[-*+]|\d+\.|#+|---)\s*)', '. ', text)
    text = re.sub(r'\n{2,}', '. ', text)
    text = text.replace('\n', ' ')
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 60]


def extract_claims_fast(text: str) -> List[Claim]:
    """
    Fast, no-LLM claim extraction using sentence splitting.
    Suitable for quick scans and fallback when LLM is unavailable.
    """
    sentences = _split_into_sentences(text)
    return [Claim(claim_id=i, action=s) for i, s in enumerate(sentences)]


# ============================================================================
#  Step 2: Claim Scoring — "The Algorithmic Judge"
# ============================================================================

_RULE_EXTRACTION_PROMPT = """You are an objective constraint inspector. Read the following prompt text given to an AI agent.

Extract every constraint, rule, requirement, restriction, format specification, or behavioral boundary as an independent string.
Return strictly a JSON array of strings with no extra text:
["rule 1 text", "rule 2 text", ...]

If the prompt contains no actionable constraints, return an empty array: []"""

_RULES_CACHE: Dict[str, List[str]] = {}

def _extract_rules_via_llm(prompt: str, client=None, model: str = None) -> List[str]:
    """Extract constraint/rule statements from a prompt via LLM."""
    if not prompt or not prompt.strip():
        return []

    cache_key = prompt.strip()
    if cache_key in _RULES_CACHE:
        return _RULES_CACHE[cache_key]

    c = client or _client
    m = model or os.environ.get("RULE_EXTRACTOR_MODEL", "gpt-4o")

    max_chars = 6000
    truncated = prompt if len(prompt) <= max_chars else prompt[:max_chars]

    try:
        response = c.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": _RULE_EXTRACTION_PROMPT},
                {"role": "user", "content": truncated}
            ],
            temperature=0.0,
        )
        content = response.choices[0].message.content if response.choices else "[]"
    except Exception:
        return _extract_rules_from_prompt(prompt)

    rules = _parse_rule_json(content)
    if not rules:
        rules = _extract_rules_from_prompt(prompt)

    _RULES_CACHE[cache_key] = rules
    if len(_RULES_CACHE) > 5000:
        keys_to_delete = list(_RULES_CACHE.keys())[:1000]
        for k in keys_to_delete:
            del _RULES_CACHE[k]

    return rules


def _parse_rule_json(raw_response: str) -> List[str]:
    """Parse LLM JSON response into a list of rule strings."""
    try:
        data = json.loads(raw_response.strip())
        if isinstance(data, list):
            return [str(item) for item in data if isinstance(item, str) and item.strip()]
    except json.JSONDecodeError:
        pass

    match = re.search(r'\[.*\]', raw_response, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return [str(item) for item in data if isinstance(item, str) and item.strip()]
        except json.JSONDecodeError:
            pass

    return []


def _extract_rules_from_prompt(prompt: str) -> List[str]:
    """[Fallback] Extract constraint/rule statements via keyword matching."""
    rules = []
    lines = prompt.split('\n')
    must_contain_keywords = ["must", "should", "require", "not", "always", "never"]
    rule_prefixes = [r"^\s*-\s+", r"^\s*\*\s+", r"^\s*\d+\.\s+"]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        is_rule = False
        for prefix in rule_prefixes:
            if re.match(prefix, line):
                is_rule = True
                break

        if not is_rule:
            line_lower = line.lower()
            if any(kw in line_lower for kw in must_contain_keywords):
                is_rule = True

        if "here is the task" in line.lower() or "according to" in line.lower():
            is_rule = False

        if is_rule:
            rules.append(line)

    return rules


class ClaimScorer:
    """
    Step 2: Algorithmic "ruthless judge."
    Computes evaluation scores for claims using embedding-based similarity
    and anchor-point deviation (as described in TODO.md).

    All scores designed for human review — no classification is performed.
    Future ErrorLocator / ErrorClassifier layers will consume these scores.
    """

    def __init__(self, embedding_model: str = "text-embedding-3-small"):
        self.embedding_model = embedding_model

    # ---- Support Score (FM-2.2 / FM-2.3: hallucination / drift) ----

    def compute_support_scores(
        self,
        claims: List[Claim],
        task_prompt: str,
    ) -> Tuple[List[SupportScoreDetail], float]:
        """
        Compute groundedness of each claim against the initial task prompt (FM-2.2/2.3).

        Each claim's embedding is compared with every sentence in the task prompt.
        The best cosine similarity becomes the claim's support score.
        Low scores indicate the claim has drifted away from the original task —
        the defining symptom of goal drift / hallucination.

        Returns:
            (per_claim_details, aggregate_score)
            aggregate_score is min across all claims (the weakest link).
        """
        if not claims:
            return [], 0.5

        context_sentences: List[str] = _split_into_sentences(task_prompt)

        if not context_sentences:
            return [SupportScoreDetail(
                claim_id=c.claim_id,
                claim_text=c.action,
                best_support_context="",
                grounded_score=0.5
            ) for c in claims], 0.5

        claim_texts = [c.action for c in claims]
        claim_embs = get_embeddings_batch(claim_texts, model=self.embedding_model)
        context_embs = get_embeddings_batch(context_sentences, model=self.embedding_model)

        details: List[SupportScoreDetail] = []
        scores: List[float] = []

        for claim, claim_vec in zip(claims, claim_embs):
            max_sim = -1.0
            best_context = ""
            for cs, c_vec in zip(context_sentences, context_embs):
                sim = cosine_similarity(claim_vec, c_vec)
                if sim > max_sim:
                    max_sim = sim
                    best_context = cs

            scores.append(max_sim)
            details.append(SupportScoreDetail(
                claim_id=claim.claim_id,
                claim_text=claim.action,
                best_support_context=best_context,
                grounded_score=round(float(max_sim), 4)
            ))

        aggregate = round(float(min(scores)), 4) if scores else 1.0
        return details, aggregate

    # ---- Norm Compliance Score (FM-1.1 / FM-1.2: constraint/role violation) ----

    def compute_norm_scores(
        self,
        output_text: str,
        rules: List[str],
    ) -> Tuple[List[NormScoreDetail], float]:
        """
        Compute constraint compliance using anchor-point deviation.

        For each rule constructs two anchors:
          Compliance:  "Obey these rules: {rule}"
          Violation:   "Don't obey these rules: {rule}"

        Delta = cos_sim(output, compliance) - cos_sim(output, violation).
        Delta > 0 means closer to compliance.

        Returns:
            (per_rule_details, aggregate_score)
            aggregate_score is min Delta across all rules.
        """
        if not rules or not output_text.strip():
            return [], 0.5

        output_vec = get_embedding(output_text, model=self.embedding_model)
        details: List[NormScoreDetail] = []
        all_scores: List[float] = []

        for rule in rules:
            pos_str = f"Obey these rules: {rule}"
            neg_str = f"Don't obey these rules: {rule}"

            pos_vec = get_embedding(pos_str, model=self.embedding_model)
            neg_vec = get_embedding(neg_str, model=self.embedding_model)

            pass_score = cosine_similarity(output_vec, pos_vec)
            fail_score = cosine_similarity(output_vec, neg_vec)

            score = pass_score - fail_score
            all_scores.append(score)
            details.append(NormScoreDetail(
                rule=rule,
                pass_score=round(float(pass_score), 4),
                fail_score=round(float(fail_score), 4),
                score=round(float(score), 4)
            ))

        aggregate = round(float(min(all_scores)), 4) if all_scores else 1.0
        return details, aggregate

    # ---- Repetition Score (FM-1.3: stuck loop / step repetition) ----

    def compute_repetition_score(
        self,
        current_output: str,
        past_outputs: List[str],
    ) -> Tuple[float, int]:
        """
        Compute how similar the current output is to recent past outputs.

        Returns:
            (repetition_score, reference_index)
            score: 0 = novel, 1 = identical to a previous output.
        """
        if not past_outputs or not current_output.strip():
            return 0.0, -1

        current_vec = get_embedding(current_output, model=self.embedding_model)

        max_sim = -1.0
        ref_idx = -1
        for i, past in enumerate(past_outputs):
            if not past.strip():
                continue
            past_vec = get_embedding(past, model=self.embedding_model)
            sim = cosine_similarity(current_vec, past_vec)
            if sim > max_sim:
                max_sim = sim
                ref_idx = i

        return round(float(max(0.0, max_sim)), 4), ref_idx

    # ---- Plan-Action Alignment (FM-2.6: plan-action gap) ----

    def compute_plan_action_alignment(
        self,
        plan_steps: List[str],
        action_descriptions: List[str],
    ) -> float:
        """
        Compute alignment between planned steps and executed actions (FM-2.6).

        Each action description is matched against the best-matching plan step.
        The aggregate is the mean across all actions (holistic coverage check).

        Returns:
            alignment_score: 0 = actions unrelated to plan (gap), 1 = perfectly aligned.
        """
        if not plan_steps or not action_descriptions:
            return 0.5

        plan_vecs = get_embeddings_batch(plan_steps, model=self.embedding_model)
        action_vecs = get_embeddings_batch(action_descriptions, model=self.embedding_model)

        scores = []
        for av in action_vecs:
            max_sim = max(cosine_similarity(av, pv) for pv in plan_vecs) if plan_vecs else 1.0
            scores.append(max_sim)

        return round(float(np.mean(scores)), 4) if scores else 1.0


# ============================================================================
#  FM-2.6 Plan / Action extraction utilities
# ============================================================================

_PLAN_EXTRACTION_PROMPT = """You are an objective plan extractor. Read the following text from a software agent.

Extract every planned architecture decision, file to create, class/function/method to implement,
or structural intent as an independent string. These are statements of intent — what the agent
SAYS it will do.

Return strictly a JSON array of strings with no extra text:
["planned item 1", "planned item 2", ...]

If the text contains no explicit plans, return an empty array: []"""

_ACTION_EXTRACTION_PROMPT = """You are an objective action extractor. Read the following text from a software agent.

Extract every actually implemented or executed action as an independent string. Focus on:
- Actual file names created
- Actual function/class/method names implemented
- Actual code logic written (not planned)
- Actual commands or API calls executed

Return strictly a JSON array of strings with no extra text:
["implemented action 1", "implemented action 2", ...]

If the text contains no implemented actions, return an empty array: []"""


def _extract_plan_steps_via_llm(output_text: str, client=None, model: str = None) -> List[str]:
    """Extract planned architecture/design steps from agent output via LLM."""
    if not output_text or not output_text.strip():
        return []

    c = client or _client
    m = model or os.environ.get("PLAN_EXTRACTOR_MODEL", "gpt-4o")
    truncated = output_text[:6000] if len(output_text) > 6000 else output_text

    try:
        response = c.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": _PLAN_EXTRACTION_PROMPT},
                {"role": "user", "content": truncated}
            ],
            temperature=0.0,
        )
        content = response.choices[0].message.content if response.choices else "[]"
        return _parse_rule_json(content)
    except Exception:
        return _extract_plan_steps_fast(output_text)


def _extract_actions_via_llm(output_text: str, client=None, model: str = None) -> List[str]:
    """Extract actually implemented actions from agent output via LLM."""
    if not output_text or not output_text.strip():
        return []

    c = client or _client
    m = model or os.environ.get("ACTION_EXTRACTOR_MODEL", "gpt-4o")
    truncated = output_text[:6000] if len(output_text) > 6000 else output_text

    try:
        response = c.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": _ACTION_EXTRACTION_PROMPT},
                {"role": "user", "content": truncated}
            ],
            temperature=0.0,
        )
        content = response.choices[0].message.content if response.choices else "[]"
        return _parse_rule_json(content)
    except Exception:
        return _extract_actions_fast(output_text)


def _extract_plan_steps_fast(output_text: str) -> List[str]:
    """[Fallback] Extract plan steps via regex from ChatDev-style output.

    Looks for architecture planning sections (Step 1/2, numbered lists before code blocks).
    """
    if not output_text:
        return []

    # Extract the planning portion: text before the first code block
    code_block_start = output_text.find('```')
    plan_section = output_text[:code_block_start] if code_block_start > 0 else output_text

    steps = []
    # Match numbered items: "1. **filename.py**: description" or "- **function_name(args)**: description"
    for pattern in [
        r'(?:\d+\.\s*\*\*|-\s+\*\*)([^*]+)\*\*:?\s*(.+?)(?=\n|$)',
        r'(?:###\s+Step\s+\d+[:\s].+)',
        r'We will create[^.]+\.',
        r'(?:^|\n)\s*[-*]\s+([A-Z][^.]+\.)',
    ]:
        for match in re.finditer(pattern, plan_section, re.MULTILINE):
            step = match.group(0).strip()
            if len(step) > 10:
                steps.append(step)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for s in steps:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique[:30]


def _extract_actions_fast(output_text: str) -> List[str]:
    """[Fallback] Extract implemented actions via regex from ChatDev-style output.

    Extracts actual file names, function/class definitions from code blocks.
    """
    if not output_text:
        return []

    actions = []
    # Extract file names from FILENAME lines before code blocks
    for m in re.finditer(r'^([a-zA-Z_][\w]*\.py)\s*$', output_text, re.MULTILINE):
        actions.append(f"Created file: {m.group(1)}")

    # Extract function definitions from code blocks
    for m in re.finditer(r'def\s+(\w+)\s*\(', output_text):
        actions.append(f"Implemented function: {m.group(1)}()")

    # Extract class definitions from code blocks
    for m in re.finditer(r'class\s+(\w+)', output_text):
        actions.append(f"Implemented class: {m.group(1)}")

    # Deduplicate preserving order
    seen = set()
    unique = []
    for a in actions:
        if a not in seen:
            seen.add(a)
            unique.append(a)
    return unique[:50]


# ============================================================================
#  Orchestrator: BugDetector
# ============================================================================

class BugDetector:
    """
    Two-step pipeline orchestrator. Covers all four fault modes.

    Usage::

        detector = BugDetector()
        scored = detector.analyze_playbook("path/to/playbook.json")

        for ix in scored.interactions:
            print(f"Turn {ix.playbook_turn}: "
                  f"support(FM-2.2/2.3)={ix.aggregate_support_score:.3f}, "
                  f"norm(FM-1.1/1.2)={ix.aggregate_norm_score:.3f}, "
                  f"rep(FM-1.3)={ix.repetition_score:.3f}, "
                  f"plan-action(FM-2.6)={ix.plan_action_alignment_score:.3f}")
    """

    def __init__(
        self,
        use_llm_extraction: bool = True,
        embedding_model: str = "text-embedding-3-small",
        llm_model: str = None,
        repetition_window: int = 3,
    ):
        self.use_llm_extraction = use_llm_extraction
        self.repetition_window = repetition_window

        self.extractor = ClaimExtractor(client=_client, model=llm_model) if use_llm_extraction else None
        self.scorer = ClaimScorer(embedding_model=embedding_model)

    # ---- Single Interaction Analysis ----

    def analyze_interaction(
        self,
        prompt: str,
        output: str,
        task_prompt: str,
        historical_outputs: List[str],
        role: str = "Unknown",
        turn: int = 0,
        phase: str = "Unknown",
        phase_turn: int = 0,
        node_index: int = -1,
    ) -> InteractionScores:
        """
        Run the full two-step pipeline on a single interaction.

        Args:
            prompt: The prompt given to the agent.
            output: The agent's output.
            task_prompt: The initial task description (for FM-2.2/2.3 drift detection).
            historical_outputs: Outputs from previous turns (for repetition check).
            role, turn, phase, phase_turn, node_index: Metadata for traceability.

        Returns:
            InteractionScores with all computed scores.
        """
        # Step 1: Extract claims
        if self.use_llm_extraction and self.extractor is not None:
            claims = self.extractor.extract_claims(output)
        else:
            claims = extract_claims_fast(output)

        # Step 2a: Support scores — groundedness against the initial task (FM-2.2/2.3)
        support_details, support_agg = self.scorer.compute_support_scores(
            claims, task_prompt
        )

        # Step 2b: Norm compliance scores — rules extracted via LLM (FM-1.1/1.2)
        rules = _extract_rules_via_llm(prompt, client=_client)
        norm_details, norm_agg = self.scorer.compute_norm_scores(output, rules)

        # Step 2c: Repetition score
        repetition_score, repetition_ref = self.scorer.compute_repetition_score(
            output, historical_outputs[-self.repetition_window:]
        )

        # Step 2d: Plan-Action alignment (FM-2.6)
        plan_steps = _extract_plan_steps_via_llm(output, client=_client)
        action_descriptions = _extract_actions_via_llm(output, client=_client)
        plan_action_align = self.scorer.compute_plan_action_alignment(plan_steps, action_descriptions)

        # Overall health: weighted composite
        # support (0–1) → 0.30 | norm mapped → 0.25 | rep inverted → 0.20 | plan-action → 0.25
        norm_mapped = (norm_agg + 1.0) / 2.0
        repetition_inverted = 1.0 - repetition_score

        health = (
            0.30 * support_agg +
            0.25 * norm_mapped +
            0.20 * repetition_inverted +
            0.25 * plan_action_align
        )

        return InteractionScores(
            role=role,
            playbook_turn=turn,
            phase=phase,
            phase_turn=phase_turn,
            node_index=node_index,
            claims=claims,
            num_claims=len(claims),
            support_score_details=support_details,
            aggregate_support_score=support_agg,
            norm_score_details=norm_details,
            aggregate_norm_score=norm_agg,
            repetition_score=repetition_score,
            repetition_reference_turn=repetition_ref,
            plan_action_alignment_score=plan_action_align,
            plan_steps=plan_steps,
            action_descriptions=action_descriptions,
            overall_health_score=round(health, 4),
            prompt_snippet=prompt[:200] + "..." if len(prompt) > 200 else prompt,
            output_snippet=output[:200] + "..." if len(output) > 200 else output,
        )

    # ---- Playbook Analysis ----

    def analyze_playbook(
        self,
        playbook_path: str,
        api_records_path: Optional[str] = None,
        task_prompt: Optional[str] = None,
    ) -> ScoredPlaybook:
        """
        Analyze a complete playbook, returning scored results.

        Args:
            playbook_path: Path to playbook.json.
            api_records_path: Optional path to api_records.jsonl for node_index resolution.
            task_prompt: The actual user task prompt. If None, falls back to
                         _extract_task_prompt(playbook) which returns the first
                         interaction prompt (typically the system prompt —
                         correct only as a last resort).

        Returns:
            ScoredPlaybook with per-interaction scores and summary statistics.
        """
        with open(playbook_path, 'r', encoding='utf-8') as f:
            playbook = json.load(f)

        interactions: List[InteractionScores] = []
        matched_indices: set = set()

        if task_prompt is None:
            task_prompt = _extract_task_prompt(playbook)

        for role, role_interactions in playbook.items():
            if not isinstance(role_interactions, list):
                continue

            for i, interaction in enumerate(role_interactions):
                prompt = interaction.get('prompt', '')
                output = interaction.get('output', '')

                hist_outputs = [
                    ri.get('output', '')
                    for ri in role_interactions[max(0, i - self.repetition_window) : i]
                ]

                node_idx = -1
                if api_records_path and os.path.exists(api_records_path):
                    node_idx = _find_node_index(api_records_path, prompt, output, matched_indices)

                scored = self.analyze_interaction(
                    prompt=prompt,
                    output=output,
                    task_prompt=task_prompt,
                    historical_outputs=hist_outputs,
                    role=role,
                    turn=interaction.get('turn', i + 1),
                    phase=interaction.get('phase', 'Unknown'),
                    phase_turn=interaction.get('phase_turn', 0),
                    node_index=node_idx,
                )
                interactions.append(scored)

        result = ScoredPlaybook(
            source_playbook_path=playbook_path,
            source_api_records_path=api_records_path or "",
            interactions=interactions,
            num_interactions=len(interactions),
            num_roles=len(playbook),
            roles=list(playbook.keys()),
        )

        if interactions:
            supports = [s.aggregate_support_score for s in interactions]
            norms = [s.aggregate_norm_score for s in interactions]
            reps = [s.repetition_score for s in interactions]
            aligns = [s.plan_action_alignment_score for s in interactions]
            healths = [s.overall_health_score for s in interactions]

            result.support_score_mean = round(float(np.mean(supports)), 4)
            result.support_score_min = round(float(np.min(supports)), 4)
            result.norm_score_mean = round(float(np.mean(norms)), 4)
            result.norm_score_min = round(float(np.min(norms)), 4)
            result.repetition_score_mean = round(float(np.mean(reps)), 4)
            result.repetition_score_max = round(float(np.max(reps)), 4)
            result.plan_action_score_mean = round(float(np.mean(aligns)), 4)
            result.plan_action_score_min = round(float(np.min(aligns)), 4)
            result.health_score_mean = round(float(np.mean(healths)), 4)
            result.health_score_min = round(float(np.min(healths)), 4)

            for role in result.roles:
                role_ixs = [s for s in interactions if s.role == role]
                if not role_ixs:
                    continue
                result.per_role_summary[role] = {
                    "num_turns": len(role_ixs),
                    "support_mean__fm_2_2_2_3": round(float(np.mean([s.aggregate_support_score for s in role_ixs])), 4),
                    "support_min__fm_2_2_2_3": round(float(np.min([s.aggregate_support_score for s in role_ixs])), 4),
                    "norm_mean__fm_1_1_1_2": round(float(np.mean([s.aggregate_norm_score for s in role_ixs])), 4),
                    "norm_min__fm_1_1_1_2": round(float(np.min([s.aggregate_norm_score for s in role_ixs])), 4),
                    "repetition_mean__fm_1_3": round(float(np.mean([s.repetition_score for s in role_ixs])), 4),
                    "repetition_max__fm_1_3": round(float(np.max([s.repetition_score for s in role_ixs])), 4),
                    "plan_action_mean__fm_2_6": round(float(np.mean([s.plan_action_alignment_score for s in role_ixs])), 4),
                    "plan_action_min__fm_2_6": round(float(np.min([s.plan_action_alignment_score for s in role_ixs])), 4),
                    "health_mean": round(float(np.mean([s.overall_health_score for s in role_ixs])), 4),
                    "health_min": round(float(np.min([s.overall_health_score for s in role_ixs])), 4),
                }

        return result

    def analyze_playbooks_batch(
        self,
        playbook_paths: List[str],
    ) -> List[ScoredPlaybook]:
        """Batch-analyze multiple playbooks."""
        results = []
        for pp in playbook_paths:
            api_path = os.path.join(os.path.dirname(pp), "api_records.jsonl")
            if not os.path.exists(api_path):
                api_path = None
            try:
                result = self.analyze_playbook(pp, api_path)
                results.append(result)
            except Exception as e:
                import sys
                print(f"[BugDetector] Error analyzing {pp}: {e}", file=sys.stderr)
        return results


# ============================================================================
#  Helper: extract initial task prompt from playbook
# ============================================================================

def _extract_task_prompt(playbook: dict) -> str:
    """Extract the initial task description from a playbook.

    Returns the first non-empty prompt found across all roles.
    Falls back to empty string if none found.
    """
    for role, interactions in playbook.items():
        if not isinstance(interactions, list) or not interactions:
            continue
        prompt = interactions[0].get('prompt', '')
        if prompt.strip():
            return prompt
    return ""

# ============================================================================
#  Helper: node index resolution from api_records.jsonl
# ============================================================================

def _find_node_index(
    api_records_path: str,
    prompt: str,
    output: str,
    matched_indices: set,
) -> int:
    """Find the 1-indexed line number in api_records.jsonl matching this output."""
    if not os.path.exists(api_records_path):
        return -1

    normalized_output = output.strip()
    prefix_length = min(100, len(normalized_output))
    target_prefix = normalized_output[:prefix_length]

    with open(api_records_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            if i in matched_indices:
                continue
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            record_output = record.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
            if record_output.strip().startswith(target_prefix):
                matched_indices.add(i)
                return i
    return -1


# ============================================================================
#  Backward-compatible wrappers
# ============================================================================

_default_detector = None

def _get_default_detector() -> BugDetector:
    global _default_detector
    if _default_detector is None:
        _default_detector = BugDetector(use_llm_extraction=True)
    return _default_detector


def check_constraint_violation(
    prompt: str, output: str, threshold: float = 0.05
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    [Backward-compatible] Check if output violates prompt constraints.
    Returns (has_bug, violations_list).
    """
    rules = _extract_rules_via_llm(prompt, client=_client)
    if not rules:
        return False, []

    output_vec = get_embedding(output)
    violations = []
    has_bug = False

    for rule in rules:
        pos_str = f"Obey these rules: {rule}"
        neg_str = f"Don't obey these rules: {rule}"
        pos_vec = get_embedding(pos_str)
        neg_vec = get_embedding(neg_str)

        pass_score = cosine_similarity(output_vec, pos_vec)
        fail_score = cosine_similarity(output_vec, neg_vec)
        score = pass_score - fail_score

        if score < threshold:
            has_bug = True
            violations.append({
                "rule": rule,
                "pass_score": pass_score,
                "fail_score": fail_score,
                "score": score,
                "threshold_used": threshold,
            })

    return has_bug, violations


def check_hallucination_bug(
    output_text: str,
    task_prompt: str,
    threshold: float = 0.5,
    aggregation: str = 'min',
) -> Tuple[bool, float, List[Dict[str, Any]]]:
    """
    [Backward-compatible] Check if output contains hallucinations (FM-2.2/2.3).

    Computes groundedness of output claims against the initial task prompt.
    Returns (has_bug, eval_score, sentence_details).
    """
    claims = extract_claims_fast(output_text)
    claim_texts = [c.action for c in claims]

    context_sentences: List[str] = _split_into_sentences(task_prompt)

    if not claim_texts or not context_sentences:
        return False, 1.0, []

    claim_embs = get_embeddings_batch(claim_texts)
    context_embs = get_embeddings_batch(context_sentences)

    sentence_details = []
    all_scores = []

    for claim_text, claim_vec in zip(claim_texts, claim_embs):
        max_sim = -1.0
        best_support = ""
        for cs, c_vec in zip(context_sentences, context_embs):
            sim = cosine_similarity(claim_vec, c_vec)
            if sim > max_sim:
                max_sim = sim
                best_support = cs
        all_scores.append(max_sim)
        sentence_details.append({
            "generated_sentence": claim_text,
            "best_support_context": best_support,
            "grounded_score": max_sim,
        })

    if not all_scores:
        return False, 1.0, sentence_details

    if aggregation == 'average':
        eval_score = sum(all_scores) / len(all_scores)
    elif aggregation == 'max':
        eval_score = max(all_scores)
    else:
        eval_score = min(all_scores)

    has_bug = eval_score < threshold
    return has_bug, eval_score, sentence_details


def scan_playbook_for_bug_1_1(
    playbook_path: str,
    api_records_path: str,
    threshold: float = 0.05,
) -> List[Dict[str, Any]]:
    """[Backward-compatible] Scan playbook for Bug 1.1 (constraint violations)."""
    detector = _get_default_detector()
    scored = detector.analyze_playbook(playbook_path, api_records_path)

    bug_reports = []
    for ix in scored.interactions:
        if ix.aggregate_norm_score < threshold:
            bug_reports.append({
                "role": ix.role,
                "playbook_turn": ix.playbook_turn,
                "phase": ix.phase,
                "phase_turn": ix.phase_turn,
                "node_index": ix.node_index,
                "violations": [
                    {"rule": nd.rule, "pass_score": nd.pass_score,
                     "fail_score": nd.fail_score, "score": nd.score,
                     "threshold_used": threshold}
                    for nd in ix.norm_score_details
                ],
            })
    return bug_reports


def scan_playbook_for_bug_1_3(
    playbook_path: str,
    api_records_path: str,
    k: int = 3,
    distance_threshold: float = 0.005,
) -> List[Dict[str, Any]]:
    """[Backward-compatible] Scan playbook for Bug 1.3 (stuck loop / repetition)."""
    with open(playbook_path, 'r', encoding='utf-8') as f:
        playbook = json.load(f)

    bug_reports = []
    matched_indices: set = set()

    for role, interactions in playbook.items():
        n = len(interactions)
        if n <= k:
            continue

        for i in range(n - k):
            base = interactions[i]
            base_output = base.get('output', '')
            if not base_output.strip():
                continue

            base_vec = get_embedding(base_output)
            is_stuck = True
            loop_details = []

            for j in range(1, k + 1):
                next_output = interactions[i + j].get('output', '')
                next_vec = get_embedding(next_output)
                sim = cosine_similarity(base_vec, next_vec)
                dist = 1.0 - sim

                if dist >= distance_threshold:
                    is_stuck = False
                    break
                else:
                    loop_details.append({
                        "turn_offset": j,
                        "compare_phase": interactions[i + j].get('phase', 'Unknown'),
                        "distance": dist,
                        "similarity": sim,
                    })

            if is_stuck:
                node_idx = _find_node_index(
                    api_records_path, base.get('prompt', ''), base_output, matched_indices
                )
                bug_reports.append({
                    "role": role,
                    "playbook_turn": base.get('turn'),
                    "phase": base.get('phase', 'Unknown'),
                    "phase_turn": base.get('phase_turn', 0),
                    "node_index": node_idx,
                    "k_window": k,
                    "distance_threshold": distance_threshold,
                    "loop_details": loop_details,
                    "stuck_output_snippet": base_output[:150] + "..." if len(base_output) > 150 else base_output,
                })

    return bug_reports


def scan_playbook_for_bug_2_2(
    playbook_path: str,
    api_records_path: str,
    threshold: float = 0.5,
    aggregation: str = 'min',
) -> List[Dict[str, Any]]:
    """[Backward-compatible] Scan playbook for Bug 2.2 (hallucination/drift).

    Tests each interaction's output against the initial task prompt.
    """
    with open(playbook_path, 'r', encoding='utf-8') as f:
        playbook = json.load(f)

    task_prompt = _extract_task_prompt(playbook)
    bug_reports = []
    matched_indices: set = set()

    for role, interactions in playbook.items():
        n = len(interactions)
        for i in range(n):
            interaction = interactions[i]
            base_output = interaction.get('output', '')

            has_bug, score, details = check_hallucination_bug(
                base_output, task_prompt, threshold, aggregation
            )

            if has_bug:
                node_idx = _find_node_index(
                    api_records_path, interaction.get('prompt', ''), base_output, matched_indices
                )
                bug_reports.append({
                    "role": role,
                    "playbook_turn": interaction.get('turn'),
                    "phase": interaction.get('phase', 'Unknown'),
                    "phase_turn": interaction.get('phase_turn', 0),
                    "node_index": node_idx,
                    "k_window": k,
                    "aggregation_used": aggregation,
                    "evaluation_score": score,
                    "details": details,
                })

    return bug_reports


def scan_playbook_for_bug_2_6(
    playbook_path: str,
    api_records_path: str,
    threshold: float = 0.5,
) -> List[Dict[str, Any]]:
    """[Backward-compatible] Scan playbook for Bug 2.6 (plan-action gap).

    Extracts plan steps and executed actions from each interaction,
    computes alignment via embedding cosine similarity.
    Reports nodes where alignment falls below threshold.
    """
    with open(playbook_path, 'r', encoding='utf-8') as f:
        playbook = json.load(f)

    bug_reports = []
    matched_indices: set = set()

    for role, interactions in playbook.items():
        if not isinstance(interactions, list):
            continue
        for interaction in interactions:
            output = interaction.get('output', '')
            if not output.strip():
                continue

            plan_steps = _extract_plan_steps_via_llm(output, client=_client)
            action_descriptions = _extract_actions_via_llm(output, client=_client)

            if not plan_steps or not action_descriptions:
                continue

            scorer = ClaimScorer()
            alignment = scorer.compute_plan_action_alignment(plan_steps, action_descriptions)

            if alignment < threshold:
                node_idx = _find_node_index(
                    api_records_path, interaction.get('prompt', ''), output, matched_indices
                )
                bug_reports.append({
                    "role": role,
                    "playbook_turn": interaction.get('turn'),
                    "phase": interaction.get('phase', 'Unknown'),
                    "phase_turn": interaction.get('phase_turn', 0),
                    "node_index": node_idx,
                    "plan_action_alignment_score": alignment,
                    "threshold_used": threshold,
                    "plan_steps": plan_steps,
                    "action_descriptions": action_descriptions,
                })

    return bug_reports


# ============================================================================
#  Convenience: save ScoredPlaybook
# ============================================================================

def save_scored_playbook(scored: ScoredPlaybook, output_path: str) -> None:
    """Serialize a ScoredPlaybook to JSON for later analysis."""

    def _to_dict(obj):
        if isinstance(obj, ScoredPlaybook):
            return {
                "source_playbook_path": obj.source_playbook_path,
                "source_api_records_path": obj.source_api_records_path,
                "num_interactions": obj.num_interactions,
                "num_roles": obj.num_roles,
                "roles": obj.roles,
                "support_score_mean__fm_2_2_2_3": obj.support_score_mean,
                "support_score_min__fm_2_2_2_3": obj.support_score_min,
                "norm_score_mean__fm_1_1_1_2": obj.norm_score_mean,
                "norm_score_min__fm_1_1_1_2": obj.norm_score_min,
                "repetition_score_mean__fm_1_3": obj.repetition_score_mean,
                "repetition_score_max__fm_1_3": obj.repetition_score_max,
                "plan_action_score_mean__fm_2_6": obj.plan_action_score_mean,
                "plan_action_score_min__fm_2_6": obj.plan_action_score_min,
                "health_score_mean": obj.health_score_mean,
                "health_score_min": obj.health_score_min,
                "per_role_summary": obj.per_role_summary,
                "interactions": [_to_dict(ix) for ix in obj.interactions],
            }
        elif isinstance(obj, InteractionScores):
            return {
                "role": obj.role,
                "playbook_turn": obj.playbook_turn,
                "phase": obj.phase,
                "phase_turn": obj.phase_turn,
                "node_index": obj.node_index,
                "num_claims": obj.num_claims,
                "claims": [{"claim_id": c.claim_id, "action": c.action} for c in obj.claims],
                "aggregate_support_score__fm_2_2_2_3": obj.aggregate_support_score,
                "aggregate_norm_score__fm_1_1_1_2": obj.aggregate_norm_score,
                "repetition_score__fm_1_3": obj.repetition_score,
                "repetition_reference_turn": obj.repetition_reference_turn,
                "plan_action_alignment_score__fm_2_6": obj.plan_action_alignment_score,
                "plan_steps": obj.plan_steps,
                "action_descriptions": obj.action_descriptions,
                "overall_health_score": obj.overall_health_score,
                "support_score_details": [
                    {"claim_id": d.claim_id, "claim_text": d.claim_text,
                     "best_support_context": d.best_support_context,
                     "grounded_score": d.grounded_score}
                    for d in obj.support_score_details
                ],
                "norm_score_details": [
                    {"rule": d.rule, "pass_score": d.pass_score,
                     "fail_score": d.fail_score, "score": d.score}
                    for d in obj.norm_score_details
                ],
                "prompt_snippet": obj.prompt_snippet,
                "output_snippet": obj.output_snippet,
            }
        return obj

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(_to_dict(scored), f, ensure_ascii=False, indent=2)


# ============================================================================
#  Future extension points (reserved)
# ============================================================================

class ErrorLocator:
    """
    [RESERVED] Future error-location layer.

    Will consume InteractionScores and:
      - Identify which specific claims are problematic
      - Map claims to error categories
      - Provide turn-level diagnostics with evidence snippets
    """
    pass


class ErrorClassifier:
    """
    [RESERVED] Future error-type determination layer.

    Will consume located errors from ErrorLocator and:
      - Assign failure-mode codes (1.1–3.3)
      - Produce structured error reports with severity
      - Enable automated regression detection across runs
    """
    pass
