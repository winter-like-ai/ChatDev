"""
llm_summarizer.py — LLM Summarization Module

Implements the CLAUDE_TODO/TODO.md specification:
  Phase 1 (Prompt Engineering):  Craft prompts that make the LLM fill in
                                 structured templates for prompts and outputs.
  Phase 2 (Harness Engineering): Validate format via string matching, retry
                                 on failure, strip templates, convert to JSON.
  Phase 3 (Testing):             Process a playbook into a structured JSON
                                 dataset of atomic task/result items.

Concepts:
  - A "prompt" (任务) is decomposed into "known information" (你知道的信息)
    and "tasks to complete" (需要完成的任务).
  - An "output" (结果) is decomposed into "completed tasks" (完成的任务).
  - Each decomposed list contains atomic items — individual, non-divisible
    statements.

Usage::

    from chatdev.analyzer.llm_summarizer import LLMSummarizer

    summarizer = LLMSummarizer()

    # Summarize a single prompt
    result = summarizer.summarize_prompt(
        "Please design a 2048 game with a GUI interface"
    )
    # -> {"known_context": [...], "tasks": ["Design a 2048 game", ...]}

    # Summarize a single output
    result = summarizer.summarize_output(
        "I created main.py with pygame..."
    )
    # -> {"output": ["Created main.py with pygame", ...]}

    # Summarize an entire playbook
    result = summarizer.summarize_playbook("path/to/playbook.json")
    # -> {"CEO": [{"known_context": [...], "tasks": [...], "output": [...]}, ...]}
"""

import json
import os
import re
from typing import List, Dict, Any, Optional, Tuple

from openai import OpenAI


# ============================================================================
#  Environment & OpenAI client initialization
# ============================================================================

def _load_env():
    search_dirs = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
    ]

    possible_paths = []
    for start_dir in search_dirs:
        curr = start_dir
        while True:
            p = os.path.join(curr, ".env")
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
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line and not line.strip().startswith("#"):
                            parts = line.strip().split("=", 1)
                            if len(parts) == 2:
                                k, v = parts
                                os.environ[k.strip()] = v.strip()
                loaded_path = p
                break
            except Exception:
                continue


_load_env()

effective_base_url = os.environ.get("BASE_URL") or os.environ.get("OPENAI_BASE_URL")

_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=effective_base_url,
)


# ============================================================================
#  Prompt Templates (Prompt工程)
# ============================================================================

SUMMARIZE_PROMPT_TEMPLATE = """You are an engineering task analyst. Decompose the given task description into atomic, non-divisible items. Output exactly in this format with no extra commentary:

```
=== Known Context ===
1. <atomic piece of context information>
2. ...

=== Tasks to Complete ===
1. <atomic task item>
2. ...
```

Example:
Input: Create a Python CLI tool that calculates word frequency in a text file. It should accept a filename as argument and output the top 10 most frequent words.

Output:
```
=== Known Context ===
1. The tool must be written in Python
2. It should be a command-line interface (CLI) tool
3. The input is a text file passed via command-line argument
4. The output is the top 10 most frequent words

=== Tasks to Complete ===
1. Parse the command-line argument to get the input filename
2. Read and process the text file content
3. Split text into words and count frequencies
4. Sort by frequency and select the top 10
5. Print the results to stdout
```"""

SUMMARIZE_OUTPUT_TEMPLATE = """You are an engineering task analyst. Decompose the given result text into atomic, non-divisible completed actions. Output exactly in this format with no extra commentary:

```
=== Completed Actions ===
1. <atomic completed action>
2. ...
```

Example:
Input: I have implemented the solution. Created main.py that accepts filename from command line using sys.argv, reads the file content, splits into words, counts frequencies with collections.Counter, and prints top 10.

Output:
```
=== Completed Actions ===
1. Created main.py as the entry point
2. Parsed the command-line argument with sys.argv
3. Read the input text file content
4. Tokenized text into individual words
5. Counted word frequencies using collections.Counter
6. Sorted by frequency and printed the top 10 results
```"""


# ============================================================================
#  Regex patterns for template validation & parsing (Harness工程)
# ============================================================================

_KNOWN_INFO_PATTERN = re.compile(r"=== Known Context ===\s*")

_TASKS_TO_COMPLETE_PATTERN = re.compile(r"=== Tasks to Complete ===\s*")

_COMPLETED_TASKS_PATTERN = re.compile(r"=== Completed Actions ===\s*")

_ITEM_PATTERN = re.compile(r"^\s*(?:\d+)[.．]\s*(.*?)$", re.MULTILINE)


# ============================================================================
#  Main Class
# ============================================================================

class LLMSummarizer:
    """LLM-based summarizer that converts raw prompt/output text into
    structured atomic-item lists.

    Implements the three-phase CLAUDE_TODO/TODO.md design:
      - Phase 1 (Prompt工程):  Pre-defined templates for extraction.
      - Phase 2 (Harness工程): Format validation, retry loop, JSON conversion.
      - Phase 3 (测试):         Playbook-level batch processing.

    Args:
        client:      OpenAI client instance.  Falls back to the module-level
                     ``_client``.
        model:       Model name (default: ``gpt-4o``).
        max_retries: Number of validation-retry attempts per call (default: 3).
    """

    def __init__(
        self,
        client: Optional[Any] = None,
        model: str = "gpt-4o",
        max_retries: int = 3,
    ):
        self.client = client or _client
        self.model = model
        self.max_retries = max_retries
        self._stats = {"prompt_calls": 0, "output_calls": 0, "retries": 0}

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def summarize_prompt(self, prompt_text: str) -> Dict[str, List[str]]:
        """Summarize a raw prompt into atomic-item lists.

        The LLM extracts:
          - "known context" (背景信息 / known information)
          - "tasks to complete" (需要完成的任务)

        Args:
            prompt_text: The raw prompt text.

        Returns:
            ``{"known_context": [...], "tasks": [...]}``
        """
        if not prompt_text or not prompt_text.strip():
            return {"known_context": [], "tasks": []}

        self._stats["prompt_calls"] += 1
        content = self._llm_call(SUMMARIZE_PROMPT_TEMPLATE, prompt_text)

        for _ in range(self.max_retries):
            if self._validate_prompt_format(content):
                return self._parse_prompt_response(content)
            self._stats["retries"] += 1
            content = self._llm_call(
                SUMMARIZE_PROMPT_TEMPLATE,
                prompt_text,
                hint="请严格遵循指定的格式输出，不要添加额外内容。",
            )

        return {"known_context": [], "tasks": [prompt_text.strip()]}

    def summarize_output(self, output_text: str) -> Dict[str, List[str]]:
        """Summarize a raw output into an atomic-item list.

        The LLM extracts "completed tasks" (完成的任务).

        Args:
            output_text: The raw agent output text.

        Returns:
            ``{"output": [item1, item2, ...]}``
        """
        if not output_text or not output_text.strip():
            return {"output": []}

        self._stats["output_calls"] += 1
        content = self._llm_call(SUMMARIZE_OUTPUT_TEMPLATE, output_text)

        for _ in range(self.max_retries):
            if self._validate_output_format(content):
                return self._parse_output_response(content)
            self._stats["retries"] += 1
            content = self._llm_call(
                SUMMARIZE_OUTPUT_TEMPLATE,
                output_text,
                hint="请严格遵循指定的格式输出，不要添加额外内容。",
            )

        return {"output": [output_text.strip()]}

    def summarize_playbook(
        self,
        playbook_path: str,
        output_path: Optional[str] = None,
        verbose: bool = False,
        skip_roles: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Summarize every interaction in a playbook.

        For each role's interaction list, both ``prompt`` and ``output``
        fields are passed through the LLM summarizer.

        Args:
            playbook_path: Path to a playbook.json file.
            output_path:   If given, write the result to this JSON file.
            verbose:       Print progress information.
            skip_roles:    Optional list of role names to skip.

        Returns:
            A dict with the same role keys as the playbook, where each
            interaction contains ``known_context`` (list), ``tasks`` (list),
            and ``output`` (list) instead of the original strings.
        """
        if not os.path.exists(playbook_path):
            raise FileNotFoundError(f"Playbook not found: {playbook_path}")

        with open(playbook_path, "r", encoding="utf-8") as f:
            playbook = json.load(f)

        skip_roles = set(skip_roles or [])
        result: Dict[str, List[Dict[str, Any]]] = {}

        for role, interactions in playbook.items():
            if not isinstance(interactions, list):
                result[role] = interactions if isinstance(interactions, dict) else {}
                continue
            if role in skip_roles:
                if verbose:
                    print(f"  [SKIP] {role}")
                result[role] = interactions
                continue

            processed: List[Dict[str, Any]] = []
            for ix, interaction in enumerate(interactions):
                prompt_raw = interaction.get("prompt", "")
                output_raw = interaction.get("output", "")

                prompt_result = self.summarize_prompt(prompt_raw)
                entry = {
                    "turn": interaction.get("turn"),
                    "phase": interaction.get("phase"),
                    "phase_turn": interaction.get("phase_turn"),
                    "known_context": prompt_result.get("known_context", []),
                    "tasks": prompt_result.get("tasks", []),
                    "output": self.summarize_output(output_raw).get("output", []),
                }

                processed.append(entry)

                if verbose and (ix + 1) % 5 == 0:
                    print(f"  [{role}] {ix + 1}/{len(interactions)}")

            result[role] = processed
            if verbose:
                print(f"  [DONE] {role}: {len(processed)} interactions")

        if output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    # ------------------------------------------------------------------
    #  Validation (Harness工程 — 字符串匹配校验)
    # ------------------------------------------------------------------

    def _validate_prompt_format(self, text: str) -> bool:
        """Check if the LLM response matches the prompt template format."""
        if not text:
            return False

        has_known = bool(_KNOWN_INFO_PATTERN.search(text))
        has_tasks = bool(_TASKS_TO_COMPLETE_PATTERN.search(text))

        if not (has_known and has_tasks):
            return False

        sections = self._split_prompt_sections(text)
        known_items = _ITEM_PATTERN.findall(sections.get("known", ""))
        task_items = _ITEM_PATTERN.findall(sections.get("tasks", ""))
        return len(known_items) > 0 or len(task_items) > 0

    def _validate_output_format(self, text: str) -> bool:
        """Check if the LLM response matches the output template format."""
        if not text:
            return False

        has_completed = bool(_COMPLETED_TASKS_PATTERN.search(text))
        if not has_completed:
            return False

        sections = self._split_output_sections(text)
        items = _ITEM_PATTERN.findall(sections.get("completed", ""))
        return len(items) > 0

    # ------------------------------------------------------------------
    #  Parsing (Harness工程 — 去模版 → JSON)
    # ------------------------------------------------------------------

    def _parse_prompt_response(self, text: str) -> Dict[str, List[str]]:
        """Strip the template wrapper and extract atomic items from a
        summarised prompt response.

        Returns ``{"known_context": [...], "tasks": [...]}`` with the two
        sections separated."""
        sections = self._split_prompt_sections(text)

        known_items = _ITEM_PATTERN.findall(sections.get("known", ""))
        task_items = _ITEM_PATTERN.findall(sections.get("tasks", ""))

        known_cleaned = [item.strip() for item in known_items if item.strip()]
        tasks_cleaned = [item.strip() for item in task_items if item.strip()]

        return {"known_context": known_cleaned, "tasks": tasks_cleaned}

    def _parse_output_response(self, text: str) -> Dict[str, List[str]]:
        """Strip the template wrapper and extract atomic items from a
        summarised output response."""
        sections = self._split_output_sections(text)
        items = _ITEM_PATTERN.findall(sections.get("completed", ""))
        cleaned = [item.strip() for item in items if item.strip()]
        return {"output": cleaned}

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _llm_call(
        self,
        system_prompt: str,
        user_content: str,
        hint: str = "",
    ) -> str:
        """Call the LLM with the given prompts and return the response text."""
        messages = [{"role": "system", "content": system_prompt}]

        user_msg = user_content
        if hint:
            user_msg = f"{user_content}\n\n{hint}"

        messages.append({"role": "user", "content": user_msg})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                max_tokens=4096,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}") from e

    def _split_prompt_sections(self, text: str) -> Dict[str, str]:
        """Split a prompt template response into 'known' and 'tasks' sections."""
        sections: Dict[str, str] = {}

        known_match = _KNOWN_INFO_PATTERN.search(text)
        tasks_match = _TASKS_TO_COMPLETE_PATTERN.search(text)

        if known_match and tasks_match:
            sections["known"] = text[known_match.end() : tasks_match.start()]
            sections["tasks"] = text[tasks_match.end() :]
        elif known_match:
            sections["known"] = text[known_match.end() :]
        elif tasks_match:
            sections["tasks"] = text[tasks_match.end() :]

        return sections

    def _split_output_sections(self, text: str) -> Dict[str, str]:
        """Split an output template response into the 'completed' section."""
        match = _COMPLETED_TASKS_PATTERN.search(text)
        if match:
            return {"completed": text[match.end() :]}
        return {}

    # ------------------------------------------------------------------
    #  Statistics
    # ------------------------------------------------------------------

    @property
    def stats(self) -> Dict[str, int]:
        """Return call statistics for this summarizer instance."""
        return dict(self._stats)

    def reset_stats(self) -> None:
        """Reset call statistics."""
        self._stats = {"prompt_calls": 0, "output_calls": 0, "retries": 0}


# ============================================================================
#  Module-level convenience functions
# ============================================================================

_default_summarizer: Optional[LLMSummarizer] = None


def _get_default_summarizer() -> LLMSummarizer:
    global _default_summarizer
    if _default_summarizer is None:
        _default_summarizer = LLMSummarizer()
    return _default_summarizer


def summarize_prompt(prompt_text: str) -> Dict[str, List[str]]:
    """Module-level convenience for :meth:`LLMSummarizer.summarize_prompt`."""
    return _get_default_summarizer().summarize_prompt(prompt_text)


def summarize_output(output_text: str) -> Dict[str, List[str]]:
    """Module-level convenience for :meth:`LLMSummarizer.summarize_output`."""
    return _get_default_summarizer().summarize_output(output_text)


def summarize_playbook(
    playbook_path: str,
    output_path: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, List[Dict[str, Any]]]:
    """Module-level convenience for :meth:`LLMSummarizer.summarize_playbook`."""
    return _get_default_summarizer().summarize_playbook(
        playbook_path, output_path=output_path, verbose=verbose
    )
