"""
bug_detector.py - Log Analyzer Module

Provides Rule Non-compliance (Bug 1.1) detection functionality using OpenAI Embeddings and Cosine Similarity.
It analyzes whether an agent's output obeys the constraints defined in its prompt.
"""

import os
import json
import numpy as np
import re
from typing import List, Dict, Any, Tuple
from functools import lru_cache

def _load_env():
    # Attempt to find .env by searching upwards from current file and current working directory
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
            if parent == curr: # Reached root
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
            
    if loaded_path:
        import sys
        print(f"[LogAnalyzer] verified config from: {loaded_path}", file=sys.stderr)
    else:
        import sys
        print("[LogAnalyzer] Warning: No .env file found.", file=sys.stderr)

_load_env()

from openai import OpenAI

# Initialize the OpenAI client using explicit environment variables for key and base URL
# Try BASE_URL first (user's .env), then falling back to OPENAI_BASE_URL (standard)
effective_base_url = os.environ.get("BASE_URL") or os.environ.get("OPENAI_BASE_URL")

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=effective_base_url
)

_EMBEDDING_CACHE = {}

def get_embeddings_batch(texts: List[str], model="text-embedding-3-small") -> List[np.ndarray]:
    """
    Fetches embeddings for a list of texts using batch OpenAI API requests.
    Utilizes an internal cache to skip redundant API calls.
    """
    if not texts:
        return []
    
    results = []
    to_fetch = []
    for t in texts:
        t_clean = t.replace("\n", " ").strip()
        if not t_clean:
            # Empty text gets a zero vector
            results.append(np.zeros(1536))
            continue
            
        if t_clean in _EMBEDDING_CACHE:
            results.append(_EMBEDDING_CACHE[t_clean])
        else:
            to_fetch.append(t_clean)
            results.append(None) # placeholder
            
    if to_fetch:
        # OpenAI max batch size is usually 2048, use chunks of 500
        chunk_size = 500
        fetched_embs = []
        for i in range(0, len(to_fetch), chunk_size):
            chunk = to_fetch[i : i + chunk_size]
            resp = client.embeddings.create(input=chunk, model=model)
            fetched_embs.extend([np.array(d.embedding) for d in resp.data])
            
        # Write to cache and fill results mappings
        fetch_idx = 0
        for i, val in enumerate(results):
            if val is None:
                emb = fetched_embs[fetch_idx]
                results[i] = emb
                _EMBEDDING_CACHE[to_fetch[fetch_idx]] = emb
                fetch_idx += 1
                
        # To prevent indefinite memory growth (max 10000 limit concept)
        if len(_EMBEDDING_CACHE) > 15000:
            keys_to_delete = list(_EMBEDDING_CACHE.keys())[:5000]
            for k in keys_to_delete:
                del _EMBEDDING_CACHE[k]
                
    return results

def get_embedding(text: str, model="text-embedding-3-small") -> np.ndarray:
    """
    Fetches the embedding for a given text from OpenAI API (wrapper over batch interface).
    """
    return get_embeddings_batch([text], model=model)[0]

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Computes the cosine similarity between two numeric vectors.
    """
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    return dot_product / (norm_vec1 * norm_vec2)

def extract_rules_from_prompt(prompt: str) -> List[str]:
    """
    Extracts rule constraints from a prompt.
    This logic is designed to be easily readable and modifiable by developers.
    """
    rules = []
    lines = prompt.split('\n')
    
    # Easily modifiable filter lists
    # Includes standard rule indicators.
    must_contain_keywords = ["must", "should", "require", "not", "always", "never"]
    # Common prefixes indicating a list or a rule
    rule_prefixes = [r"^\s*-\s+", r"^\s*\*\s+", r"^\s*\d+\.\s+"]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        is_rule = False
        
        # Condition 1: Check if it starts with a common list prefix
        for prefix in rule_prefixes:
            if re.match(prefix, line):
                is_rule = True
                break
                
        # Condition 2: Check if it contains imperative keywords (case formatting invariant)
        if not is_rule:
            line_lower = line.lower()
            if any(kw in line_lower for kw in must_contain_keywords):
                is_rule = True

        # Optional: Exclude typical conversational filler or headers
        if "here is the task" in line.lower() or "according to" in line.lower():
            is_rule = False

        if is_rule:
            rules.append(line)
            
    return rules

def find_node_index(api_records_path: str, prompt: str, output: str, matched_indices: set = None) -> int:
    """
    Searches the original api_records.jsonl file to find the node index associated
    with the given output. Now uses strict physical line matching (1-indexed) to avoid
    confusion and skips already matched indices.
    """
    if not os.path.exists(api_records_path):
        return -1
        
    if matched_indices is None:
        matched_indices = set()
        
    normalized_output = output.strip()
    prefix_length = min(100, len(normalized_output))
    target_output_prefix = normalized_output[:prefix_length]
    
    with open(api_records_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, start=1):
            if i in matched_indices:
                continue
            if not line.strip():
                continue
            record = json.loads(line)
            record_output = record.get('output', {}).get('choices', [{}])[0].get('message', {}).get('content', '')
            if record_output.strip().startswith(target_output_prefix):
                matched_indices.add(i)
                return i
    return -1

def check_constraint_violation(prompt: str, output: str, threshold: float = 0.05) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Analyzes whether the output violates the rules extracted from the prompt.
    Returns a boolean (True if Bug 1.1 exists) and a list of violation details.
    
    Algorithm:
    1. Extract rules from prompt.
    2. Convert output to vector.
    3. For each rule:
       - pos_str = "Obey these rules: " + rule
       - neg_str = "Don't obey these rules: " + rule
       - vec_pos, vec_neg = get_embedding(pos_str), get_embedding(neg_str)
       - pass_score = cos_sim(output, pos_str)
       - fail_score = cos_sim(output, neg_str)
       - score = pass - fail
       - if score < threshold, flag as violation.
    """
    rules = extract_rules_from_prompt(prompt)
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
                "threshold_used": threshold
            })
            
    return has_bug, violations

def scan_playbook_for_bug_1_1(playbook_path: str, api_records_path: str, threshold: float = 0.05) -> List[Dict[str, Any]]:
    """
    Main interface intended for Jupyter Notebooks.
    Scans the playbook.json, utilizes api_records for traceability, and detects Bug 1.1 instances.
    """
    with open(playbook_path, 'r', encoding='utf-8') as f:
        playbook = json.load(f)
        
    bug_reports = []
    matched_indices = set()
    
    for role, interactions in playbook.items():
        for interaction in interactions:
            prompt = interaction.get('prompt', '')
            output = interaction.get('output', '')
            
            # Use the core evaluation logic
            has_bug, violations = check_constraint_violation(prompt, output, threshold)
            
            if has_bug:
                node_idx = find_node_index(api_records_path, prompt, output, matched_indices)
                
                report = {
                    "role": role,
                    "playbook_turn": interaction.get('turn'),
                    "phase": interaction.get('phase', 'Unknown'),
                    "phase_turn": interaction.get('phase_turn', 0),
                    "node_index": node_idx,
                    "violations": violations
                }
                bug_reports.append(report)
                
    return bug_reports

def scan_playbook_for_bug_1_3(playbook_path: str, api_records_path: str, k: int = 3, distance_threshold: float = 0.005) -> List[Dict[str, Any]]:
    """
    Scans the playbook for Bug 1.3: Tool Repetition / Stuck Loops.
    An agent is considered stuck if for a given turn i, its output's cosine distance to the outputs 
    of the subsequent k turns is strictly less than distance_threshold.
    
    Args:
        playbook_path: Path to the parsed playbook JSON.
        api_records_path: Path to the original api_records.jsonl for traceability.
        k: The number of consecutive turns that must be identical/similar to trigger the bug.
        distance_threshold: 1.0 - cosine_similarity threshold. Default 0.005 (highly identical).
    """
    with open(playbook_path, 'r', encoding='utf-8') as f:
        playbook = json.load(f)
        
    bug_reports = []
    matched_indices = set()
    
    for role, interactions in playbook.items():
        n = len(interactions)
        if n <= k:
            continue
            
        # Sliding window approach per role
        for i in range(n - k):
            base_interaction = interactions[i]
            base_output = base_interaction.get('output', '')
            if not base_output.strip():
                continue
                
            base_vec = get_embedding(base_output)
            is_stuck_loop = True
            loop_details = []
            
            for j in range(1, k + 1):
                next_interaction = interactions[i + j]
                next_output = next_interaction.get('output', '')
                next_vec = get_embedding(next_output)
                
                sim = cosine_similarity(base_vec, next_vec)
                dist = 1.0 - sim
                
                if dist >= distance_threshold:
                    is_stuck_loop = False
                    break
                else:
                    loop_details.append({
                        "turn_offset": j,
                        "compare_phase": next_interaction.get('phase', 'Unknown'),
                        "distance": dist,
                        "similarity": sim
                    })
                    
            if is_stuck_loop:
                node_idx = find_node_index(api_records_path, base_interaction.get('prompt', ''), base_output, matched_indices)
                report = {
                    "role": role,
                    "playbook_turn": base_interaction.get('turn'),
                    "phase": base_interaction.get('phase', 'Unknown'),
                    "phase_turn": base_interaction.get('phase_turn', 0),
                    "node_index": node_idx,
                    "k_window": k,
                    "distance_threshold": distance_threshold,
                    "loop_details": loop_details,
                    # We might want to include the duplicated text snapshot
                    "stuck_output_snippet": base_output[:150] + "..." if len(base_output) > 150 else base_output
                }
                bug_reports.append(report)
                
                
    return bug_reports

def remove_code_keep_comments(text: str) -> str:
    """
    Removes markdown code blocks from text, but attempts to retain comment lines.
    """
    lines = text.split('\n')
    in_code_block = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            # Keep common comment pattern lines
            if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                cleaned = re.sub(r'^(#|//|/\*|\*)\s*', '', stripped)
                if cleaned:
                    if not cleaned.endswith(('.', '!', '?')):
                        cleaned += '.'
                    new_lines.append(cleaned)
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)

def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into fine-grained sentences by natural language punctuations.
    """
    text = remove_code_keep_comments(text)
    
    # Convert markdown structures (lists, headers, rules) to periods to prevent boundary squashing
    text = re.sub(r'(?i)(?:\n\s*(?:[-*+]|\d+\.|#+|---)\s*)', '. ', text)
    # Normalize double blank lines to sentence boundaries
    text = re.sub(r'\n{2,}', '. ', text)
    
    # Normalize remaining newlines to spaces for contiguous sentence reading
    text = text.replace('\n', ' ')
    # Split by standard line-ending punctuation optionally followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Ignore empty strings or fragments; only record sentences longer than 100 characters
    return [s.strip() for s in sentences if len(s.strip()) > 100]

def check_hallucination_bug(output_text: str, historical_prompts: List[str], threshold: float = 0.05, aggregation: str = 'min') -> Tuple[bool, float, List[Dict[str, Any]]]:
    """
    Checks if the output contains hallucinations or drift based on the historical prompt context.
    Evaluates groundedness of each sentence.
    """
    output_sentences = split_into_sentences(output_text)
    if not output_sentences:
        return False, 1.0, []
        
    context_sentences = []
    for p in historical_prompts:
        context_sentences.extend(split_into_sentences(p))
        
    if not context_sentences:
        # Cannot evaluate without context
        return False, 1.0, []
        
    context_embs = get_embeddings_batch(context_sentences)
    output_embs = get_embeddings_batch(output_sentences)
    
    sentence_details = []
    all_scores = []
    
    for out_sen, out_vec in zip(output_sentences, output_embs):
        max_sim = -1.0
        best_support = ""
        
        for cs, c_vec in zip(context_sentences, context_embs):
            sim = cosine_similarity(out_vec, c_vec)
            if sim > max_sim:
                max_sim = sim
                best_support = cs
                
        all_scores.append(max_sim)
        sentence_details.append({
            "generated_sentence": out_sen,
            "best_support_context": best_support,
            "grounded_score": max_sim
        })
        
    if not all_scores:
        return False, 1.0, sentence_details
        
    if aggregation == 'average':
        eval_score = sum(all_scores) / len(all_scores)
    elif aggregation == 'max':
        eval_score = max(all_scores)
    else:
        # Default to 'min'
        eval_score = min(all_scores)
        
    has_bug = eval_score < threshold
    return has_bug, eval_score, sentence_details

def scan_playbook_for_bug_2_2(playbook_path: str, api_records_path: str, k: int = 3, threshold: float = 0.5, aggregation: str = 'min') -> List[Dict[str, Any]]:
    """
    Scans the playbook for Bug 2.2: Hallucination/Entropy Increment.
    A turn is flagged if its generated output sentences lack groundedness support 
    from the prompts of the last k turns.
    """
    with open(playbook_path, 'r', encoding='utf-8') as f:
        playbook = json.load(f)
        
    bug_reports = []
    matched_indices = set()
    
    for role, interactions in playbook.items():
        n = len(interactions)
        for i in range(n):
            interaction = interactions[i]
            
            # The context window includes the current prompt and the previous (k-1) prompts.
            start_idx = max(0, i - k + 1)
            history_interactions = interactions[start_idx : i + 1]
            historical_prompts = [hi.get('prompt', '') for hi in history_interactions]
            
            base_output = interaction.get('output', '')
            has_bug, score, details = check_hallucination_bug(base_output, historical_prompts, threshold, aggregation)
            
            if has_bug:
                node_idx = find_node_index(api_records_path, interaction.get('prompt', ''), base_output, matched_indices)
                report = {
                    "role": role,
                    "playbook_turn": interaction.get('turn'),
                    "phase": interaction.get('phase', 'Unknown'),
                    "phase_turn": interaction.get('phase_turn', 0),
                    "node_index": node_idx,
                    "k_window": k,
                    "aggregation_used": aggregation,
                    "evaluation_score": score,
                    "details": details
                }
                bug_reports.append(report)
                
    return bug_reports
