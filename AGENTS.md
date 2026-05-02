# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project overview

ChatDev is a Python framework that simulates a software company as a multi-agent workflow. A top-level run launches a `ChatChain`, which loads company configuration from the resolved company-config root (`config/` or `CompanyConfig/`), recruits role agents into a shared `ChatEnv`, executes a configured chain of phases, and writes generated artifacts plus logs under the resolved workspace root (`outputs/` or `WareHouse/`) using `<project>_<org>_<timestamp>` directories.

This branch also adds snapshot/replay-oriented work on top of the original ChatDev flow. The CLI in `run.py` supports four execution modes:
- default: normal live API execution
- snapshot: live execution plus JSONL recording and git/workspace tracking via environment variables
- replay: replay from a JSONL file without live API calls
- hybrid: replay up to a selected node, then resume live execution

## Common commands

## Environment setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The repository expects a Python 3.9+ environment. `run.py` loads `.env` automatically via `python-dotenv`.

## Run ChatDev

Default run:

```bash
python3 run.py --task "design a 2048 game" --name "2048"
```

Use a different company configuration:

```bash
python3 run.py --task "design a 2048 game" --name "2048" --config Human
python3 run.py --task "design a 2048 game" --name "2048" --config Art
python3 run.py --task "design a 2048 game" --name "2048" --config Incremental --path /path/to/existing/code
```

Run snapshot / replay / hybrid modes:

```bash
python3 run.py --task "design a 2048 game" --name "2048" --snapshot
python3 run.py --task "design a 2048 game" --name "2048" --snapshot /tmp/api_records.jsonl
python3 run.py --replay test/default_replay.jsonl
python3 run.py --hybrid test/default_replay.jsonl --hybrid-node 5
```

Outputs are written under `outputs/` and the workspace path is also exposed through `CHATDEV_WORKSPACE` during a run.

## Run generated software

After a run completes, enter the generated project directory and run its entrypoint:

```bash
python3 outputs/<project>_<org>_<timestamp>/main.py
```

## Run the visualizer

```bash
python3 visualizer/app.py --port 8000
```

The Flask app serves the static UI and replay pages from `visualizer/static/`.

## Log analyzer CLI

```bash
python -m chatdev.analyzer.cli /path/to/chatdev.log --skip-flask --skip-http
```

## Docker

Build the container:

```bash
docker build -t chatdev .
```

The `Dockerfile` installs the Python dependencies and starts an interactive shell by default.

## Tests

There is no conventional automated test suite configured in this repository right now: no `pytest.ini`, `tox.ini`, `setup.py`, `Makefile`, or standard test modules were found. The `test/` directory mainly contains notebooks, guides, captured logs, and analysis scripts rather than runnable unit tests.

If you need to validate code, prefer targeted script execution for the area you changed, for example:

```bash
python3 run.py --help
python3 visualizer/app.py --help
python -m chatdev.analyzer.cli --help
```

For a single script-style check, run the file directly, e.g.:

```bash
python3 scripts/log_analysis_pipeline.py
```

## Architecture

## Execution flow

The main orchestration path is:
1. `run.py` parses CLI flags, resolves the selected company config, sets execution-mode environment variables, and constructs `chatdev.chat_chain.ChatChain`.
2. `ChatChain` loads three JSON config files:
   - `ChatChainConfig.json`: overall chain, recruitments, feature toggles
   - `PhaseConfig.json`: per-phase prompts, role pairings, turn limits
   - `RoleConfig.json`: system prompts for each agent role
3. `ChatChain.pre_processing()` creates a timestamped workspace in `outputs/`, copies the selected config files into it, optionally copies a base code tree for incremental mode, initializes optional memory, and stores the original task prompt.
4. `ChatChain.make_recruitment()` registers the configured roles in `ChatEnv`.
5. `ChatChain.execute_chain()` walks the configured phase chain and dispatches each item either to a simple phase (`chatdev.phase`) or a composed phase (`chatdev.composed_phase`).
6. `ChatChain.post_processing()` writes `meta.txt`, emits summary statistics from the run log, optionally commits generated code if git management is enabled, and finalizes the log.

## Core runtime objects

### `chatdev/chat_chain.py`
Owns the full run lifecycle. This is the best entrypoint when changing orchestration behavior, config loading, workspace creation, or run/post-run behavior.

### `chatdev/chat_env.py`
Shared mutable state passed across phases. It contains:
- recruited agents (`Roster`)
- generated code (`Codes`)
- generated docs (`Documents` for requirements/manuals)
- optional cross-phase memory (`chatdev.memory.memory.Memory`)
- environment fields such as modality, language, review comments, error summaries, and workspace directory

`ChatEnv` also contains helper methods for running generated `main.py`, writing metadata, rewriting generated code/docs, and generating images.

### `chatdev/phase.py`
Defines `Phase`, the abstraction for a single seminar between two roles. A phase:
- pulls needed state from `ChatEnv`
- runs a `chatdev.agents.RolePlaying` conversation
- extracts a seminar conclusion, optionally via self-reflection
- pushes the result back into `ChatEnv`

Concrete simple phases live here as subclasses.

### `chatdev/composed_phase.py`
Defines higher-level loops built from simple phases. These classes control repeated execution patterns such as test/fix or review/fix cycles and decide when to break out early.

### `chatdev/codes.py` and `chatdev/documents.py`
These are the artifact writers. They parse LLM markdown output into concrete files, track in-memory versions, and write the final files into the generated workspace. `Codes` also performs per-phase git commits inside generated projects when git management is enabled.

## Configuration model

Most behavior is data-driven from `config/`.
- `config/Default/` is the fallback baseline.
- `run.py:get_config()` mixes a selected company directory with `config/Default/` file-by-file, so missing files in a custom config automatically fall back to Default.
- `Human`, `Art`, and `Incremental` are not separate codepaths in the runner; they are alternative config sets that change the chain and prompts.

When changing behavior, first decide whether it belongs in JSON config or in Python orchestration code. Many workflow changes only require config edits.

## Generated artifact model

A ChatDev run does not modify the repository source tree directly. Instead it creates a new project folder under `outputs/` containing generated code, copied config, logs, prompt text, and metadata. That means bugs in generation often need inspection of both:
- the framework code under `chatdev/`
- the produced workspace under `outputs/<run>/`

## Visualizer and logs

The visualizer is a small Flask server in `visualizer/app.py`. It serves static pages and receives messages through `/send_message`; runtime logging utilities post to it opportunistically but degrade if the Flask app is not running.

Logs are a primary product of the system. `chatdev.utils.log_visualize()` drives the human-readable run log, `chatdev.statistics.get_info()` parses those logs for run summaries, and `chatdev/analyzer/` contains a separate parser/CLI for structured analysis of those logs.

## Repository areas worth recognizing

- `chatdev/agents/`: the agent framework used by ChatDev’s phases and role-playing sessions (formerly `camel/`).
- `chatdev/memory/`: experiential co-learning and memory support used when `with_memory` is enabled (formerly `ecl/`).
- `visualizer/`: Flask + static frontend for live/replay log visualization.
- `chatdev/analyzer/`: parser and CLI for post-processing ChatDev logs (formerly `log_analyzer/`).
- `config/`: the workflow definitions you usually edit before touching orchestration code.
- `docs/ebook/`, `data/srdd/`, `data/dataset_mini/`, `outputs/`, and `outputs_old/`: datasets, demos, generated artifacts, and research assets rather than the core runtime.

## Working guidance for future changes

- Prefer checking the selected company JSON configs before editing Python. Prompt flow, role pairing, and many chain-level changes are config-driven.
- When editing generated-artifact behavior, trace both `ChatChain` and `ChatEnv` together; workspace creation, file rewriting, git behavior, and metadata writing are split across them.
- If you change snapshot/replay behavior, inspect `run.py` first because the mode selection happens there via CLI flags and environment variables before any orchestration objects are built.
