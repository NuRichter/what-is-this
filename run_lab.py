#!/usr/bin/env python3
"""
RedTeam AI Stack — Multi-File Generation Orchestrator (run_lab.py)
==================================================================
Generates 100+ files in complex folder structures from a single prompt.

This script wraps around the local LLM (Ollama/LM Studio) to:
1. Send a detailed prompt requesting multi-file output
2. Parse the structured output (=== FILE: ... === delimiters)
3. Auto-create directories and write all files to disk
4. Optionally initialize a git repo and commit

Author:  NuRichter Workspace (github.com/NuRichter)
License: MIT
Date:    May 2026

Usage:
    python run_lab.py --mode scaffold --prompt prompts/examples/recon_toolkit.md
    python run_lab.py --mode scaffold --prompt prompts/examples/c2_framework.md --output ./my-c2
    python run_lab.py --mode inline "Create a Python port scanner with 5 modules"
    python run_lab.py --mode aider --prompt prompts/examples/recon_toolkit.md --output ./existing-repo
    python run_lab.py --list-models
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

DEFAULT_MODEL = "qwen-cyber"
OLLAMA_API = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
LMSTUDIO_API = os.getenv("LMSTUDIO_HOST", "http://127.0.0.1:1234")
DEFAULT_OUTPUT = Path("./generated")
MAX_TOKENS = 8192
TEMPERATURE = 0.15

# File delimiter patterns the model is instructed to use
FILE_START_PATTERN = re.compile(
    r"^={3,}\s*FILE:\s*(.+?)\s*={3,}\s*$", re.MULTILINE
)
FILE_END_PATTERN = re.compile(
    r"^={3,}\s*END\s*FILE\s*={3,}\s*$", re.MULTILINE
)

# Alternative patterns (models sometimes deviate)
ALT_FILE_PATTERNS = [
    # ```filename or ```path/to/file
    re.compile(r"^```(\S+\.\w+)\s*$", re.MULTILINE),
    # # File: path/to/file
    re.compile(r"^#\s*File:\s*(.+?)\s*$", re.MULTILINE),
    # // path/to/file
    re.compile(r"^//\s*(.+\.\w+)\s*$", re.MULTILINE),
]

BANNER = r"""
╔══════════════════════════════════════════════════════════╗
║     🔴 RedTeam AI Lab — Multi-File Generator            ║
║     Offensive Cybersecurity Project Scaffolder           ║
╚══════════════════════════════════════════════════════════╝
"""

# ──────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────


@dataclass
class GeneratedFile:
    path: str
    content: str
    size: int = 0

    def __post_init__(self) -> None:
        self.size = len(self.content.encode("utf-8"))


@dataclass
class GenerationResult:
    files: list[GeneratedFile] = field(default_factory=list)
    raw_output: str = ""
    model: str = ""
    tokens_generated: int = 0
    duration_seconds: float = 0.0
    passes: int = 0
    errors: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# LLM API Client
# ──────────────────────────────────────────────


def call_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: str = "",
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
    stream: bool = True,
) -> str:
    """Call Ollama API and return the full response text."""
    import requests

    url = f"{OLLAMA_API}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": 32768,
            "repeat_penalty": 1.05,
        },
        "stream": stream,
    }

    full_response = []

    if stream:
        with requests.post(url, json=payload, stream=True, timeout=600) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    full_response.append(token)
                    print(token, end="", flush=True)
                    if chunk.get("done", False):
                        break
        print()  # newline after stream
    else:
        resp = requests.post(url, json=payload, timeout=600)
        resp.raise_for_status()
        data = resp.json()
        full_response.append(data.get("response", ""))

    return "".join(full_response)


def call_openai_compatible(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: str = "",
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
    api_base: str = "",
) -> str:
    """Call OpenAI-compatible API (LM Studio or Ollama /v1 endpoint)."""
    import requests

    base = api_base or f"{LMSTUDIO_API}/v1"
    url = f"{base}/chat/completions"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    resp = requests.post(
        url,
        json=payload,
        headers={"Authorization": "Bearer ollama"},
        timeout=600,
    )
    resp.raise_for_status()
    data = resp.json()

    return data["choices"][0]["message"]["content"]


# ──────────────────────────────────────────────
# Output Parser
# ──────────────────────────────────────────────


def parse_multi_file_output(raw: str) -> list[GeneratedFile]:
    """
    Parse LLM output containing multiple file definitions.

    Supports primary format:
        === FILE: path/to/file.ext ===
        <content>
        === END FILE ===

    And fallback patterns for common model deviations.
    """
    files: list[GeneratedFile] = []

    # Strategy 1: Primary delimiter format
    starts = list(FILE_START_PATTERN.finditer(raw))
    if starts:
        for i, match in enumerate(starts):
            filepath = match.group(1).strip().strip('"').strip("'")
            content_start = match.end()

            # Find the next END FILE or next FILE start
            end_match = FILE_END_PATTERN.search(raw, content_start)
            if end_match:
                content = raw[content_start : end_match.start()]
            elif i + 1 < len(starts):
                content = raw[content_start : starts[i + 1].start()]
            else:
                content = raw[content_start:]

            content = content.strip("\n")

            # Remove markdown code fences if the model wrapped content
            content = re.sub(r"^```\w*\n", "", content)
            content = re.sub(r"\n```\s*$", "", content)

            if filepath and content:
                files.append(GeneratedFile(path=filepath, content=content))

        return files

    # Strategy 2: Markdown code blocks with filenames
    # ```python filename.py or ```filename.py
    block_pattern = re.compile(
        r"```(?:\w+\s+)?(\S+\.\w+)\s*\n(.*?)```",
        re.DOTALL,
    )
    blocks = list(block_pattern.finditer(raw))
    if blocks:
        for m in blocks:
            filepath = m.group(1).strip()
            content = m.group(2).strip()
            if filepath and content:
                files.append(GeneratedFile(path=filepath, content=content))
        return files

    # Strategy 3: Look for "# File: path" or "// File: path" headers
    header_pattern = re.compile(
        r"(?:^|\n)(?:#|//)\s*(?:File|file):\s*(.+?)\s*\n```\w*\n(.*?)```",
        re.DOTALL,
    )
    headers = list(header_pattern.finditer(raw))
    if headers:
        for m in headers:
            filepath = m.group(1).strip()
            content = m.group(2).strip()
            if filepath and content:
                files.append(GeneratedFile(path=filepath, content=content))
        return files

    # Strategy 4: If nothing parsed, treat entire output as single file
    if raw.strip():
        # Try to detect language for extension
        if "def " in raw or "import " in raw:
            ext = ".py"
        elif "#include" in raw:
            ext = ".c"
        elif "function " in raw or "const " in raw:
            ext = ".js"
        else:
            ext = ".txt"
        files.append(GeneratedFile(path=f"output{ext}", content=raw.strip()))

    return files


# ──────────────────────────────────────────────
# File Writer
# ──────────────────────────────────────────────


def write_files(
    files: list[GeneratedFile],
    output_dir: Path,
    git_init: bool = True,
) -> int:
    """Write parsed files to disk, creating directories as needed."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0

    for f in files:
        # Sanitize path — prevent directory traversal
        clean_path = Path(f.path.lstrip("/\\").replace("..", ""))
        full_path = output_dir / clean_path

        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        try:
            full_path.write_text(f.content, encoding="utf-8")
            written += 1
            size_kb = f.size / 1024
            print(f"  📄 {clean_path} ({size_kb:.1f} KB)")
        except Exception as e:
            print(f"  ❌ Failed to write {clean_path}: {e}")

    # Git init and commit
    if git_init and written > 0:
        git_dir = output_dir / ".git"
        if not git_dir.exists():
            subprocess.run(["git", "init"], cwd=output_dir, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=output_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial scaffold by RedTeam AI Stack"],
            cwd=output_dir,
            capture_output=True,
        )
        print(f"\n  📦 Git repo initialized with {written} files committed")

    return written


# ──────────────────────────────────────────────
# Multi-Pass Generator
# ──────────────────────────────────────────────


def generate_multipass(
    prompt: str,
    model: str = DEFAULT_MODEL,
    output_dir: Path = DEFAULT_OUTPUT,
    max_passes: int = 5,
    target_files: int = 20,
    api_mode: str = "ollama",
    git_init: bool = True,
) -> GenerationResult:
    """
    Generate a multi-file project using iterative LLM calls.

    Because the model's output token limit (~8K) can't emit 100+ files
    in one call, this function loops: it asks for the project structure first,
    then generates files in batches, tracking which files are done.
    """
    result = GenerationResult(model=model)
    start_time = time.time()

    system_prompt = (
        "You are an offensive-security software engineer. "
        "Generate complete, runnable code files. "
        "For EVERY file, use this exact format:\n\n"
        "=== FILE: path/to/file.ext ===\n"
        "<complete file content>\n"
        "=== END FILE ===\n\n"
        "Generate as many files as possible per response. "
        "No explanations, disclaimers, or commentary — only code files."
    )

    all_files: dict[str, GeneratedFile] = {}

    for pass_num in range(1, max_passes + 1):
        print(f"\n{'─' * 50}")
        print(f"  Pass {pass_num}/{max_passes} — {len(all_files)} files so far")
        print(f"{'─' * 50}\n")

        if pass_num == 1:
            current_prompt = prompt
        else:
            existing = "\n".join(f"  - {p}" for p in sorted(all_files.keys()))
            current_prompt = (
                f"Continue generating the project. "
                f"Files already created:\n{existing}\n\n"
                f"Generate the REMAINING files that haven't been created yet. "
                f"Original specification:\n{prompt}"
            )

        try:
            if api_mode == "ollama":
                raw = call_ollama(
                    prompt=current_prompt,
                    model=model,
                    system=system_prompt,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                )
            else:
                raw = call_openai_compatible(
                    prompt=current_prompt,
                    model=model,
                    system=system_prompt,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    api_base=f"{LMSTUDIO_API}/v1" if api_mode == "lmstudio" else f"{OLLAMA_API}/v1",
                )
        except Exception as e:
            result.errors.append(f"Pass {pass_num} API error: {e}")
            print(f"\n  ❌ API call failed: {e}")
            break

        result.raw_output += raw + "\n\n"
        result.passes = pass_num

        # Parse files from this pass
        new_files = parse_multi_file_output(raw)
        new_count = 0
        for f in new_files:
            if f.path not in all_files:
                all_files[f.path] = f
                new_count += 1

        print(f"\n  → Parsed {len(new_files)} files ({new_count} new)")

        # Check if we've reached the target or model stopped producing new files
        if len(all_files) >= target_files:
            print(f"  ✅ Reached target of {target_files}+ files")
            break
        if new_count == 0:
            print("  ⚠️  No new files generated — stopping")
            break

    # Write all files to disk
    result.files = list(all_files.values())
    result.duration_seconds = time.time() - start_time

    if result.files:
        print(f"\n{'═' * 50}")
        print(f"  Writing {len(result.files)} files to {output_dir}")
        print(f"{'═' * 50}\n")
        written = write_files(result.files, output_dir, git_init=git_init)
        result.tokens_generated = len(result.raw_output.split())

        print(f"\n{'═' * 50}")
        print(f"  GENERATION COMPLETE")
        print(f"  Files:    {written}")
        print(f"  Passes:   {result.passes}")
        print(f"  Duration: {result.duration_seconds:.1f}s")
        print(f"  Output:   {output_dir.resolve()}")
        print(f"{'═' * 50}")
    else:
        print("\n  ❌ No files were generated. Check model and prompt.")

    return result


# ──────────────────────────────────────────────
# Aider Integration
# ──────────────────────────────────────────────


def run_aider_scaffold(
    prompt: str,
    model: str = DEFAULT_MODEL,
    output_dir: Path = DEFAULT_OUTPUT,
) -> None:
    """Use Aider to scaffold a project in an existing or new repo."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize git if needed
    git_dir = output_dir / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init"], cwd=output_dir, capture_output=True)
        # Create a dummy file so git has something to track
        (output_dir / ".gitkeep").touch()
        subprocess.run(["git", "add", "."], cwd=output_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=output_dir,
            capture_output=True,
        )

    # Copy Aider configs
    stack_root = Path.home() / "RedTeamStack" / "configs"
    for cfg in [".aider.conf.yml", ".aider.model.settings.yml"]:
        src = stack_root / cfg
        dst = output_dir / cfg
        if src.exists() and not dst.exists():
            import shutil
            shutil.copy2(src, dst)

    # Run Aider with the prompt
    cmd = [
        "aider",
        "--model", f"ollama_chat/{model}",
        "--message", prompt,
        "--yes",  # auto-accept file creation
    ]

    print(f"\n  Launching Aider in {output_dir}...")
    print(f"  Command: {' '.join(cmd)}\n")

    subprocess.run(cmd, cwd=output_dir)


# ──────────────────────────────────────────────
# GPT-Engineer Integration
# ──────────────────────────────────────────────


def run_gpte_scaffold(
    prompt: str,
    output_dir: Path = DEFAULT_OUTPUT,
) -> None:
    """Use GPT-Engineer to scaffold a project from a prompt file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write prompt file
    prompt_file = output_dir / "prompt"
    prompt_file.write_text(prompt, encoding="utf-8")

    # Set environment
    env = os.environ.copy()
    env["OPENAI_API_BASE"] = f"{OLLAMA_API}/v1"
    env["OPENAI_API_KEY"] = "ollama"
    env["MODEL_NAME"] = DEFAULT_MODEL

    cmd = ["gpte", str(output_dir), "--lite", "--temperature", "0.1"]

    print(f"\n  Launching GPT-Engineer in {output_dir}...")
    print(f"  Command: {' '.join(cmd)}\n")

    subprocess.run(cmd, env=env)


# ──────────────────────────────────────────────
# Utility Functions
# ──────────────────────────────────────────────


def list_models() -> None:
    """List available Ollama models."""
    try:
        import requests
        resp = requests.get(f"{OLLAMA_API}/api/tags", timeout=10)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            print("\n  Available Ollama models:")
            print(f"  {'Name':<45} {'Size':<12} {'Modified'}")
            print(f"  {'─' * 45} {'─' * 12} {'─' * 20}")
            for m in models:
                name = m.get("name", "")
                size_gb = m.get("size", 0) / (1024**3)
                modified = m.get("modified_at", "")[:19]
                print(f"  {name:<45} {size_gb:.1f} GB     {modified}")
        else:
            print(f"  ❌ Ollama API returned {resp.status_code}")
    except Exception as e:
        print(f"  ❌ Cannot reach Ollama: {e}")


# ──────────────────────────────────────────────
# Main CLI
# ──────────────────────────────────────────────


def main() -> None:
    print(BANNER)

    parser = argparse.ArgumentParser(
        description="RedTeam AI Lab — Multi-File Generation Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python run_lab.py --mode scaffold --prompt prompts/examples/recon_toolkit.md
          python run_lab.py --mode scaffold --prompt prompts/examples/c2_framework.md --output ./my-c2
          python run_lab.py --mode inline "Create a Python keylogger with 10 modules"
          python run_lab.py --mode aider --prompt prompts/examples/recon_toolkit.md
          python run_lab.py --mode gpte --prompt prompts/examples/c2_framework.md
          python run_lab.py --list-models
        """),
    )

    parser.add_argument(
        "--mode",
        choices=["scaffold", "inline", "aider", "gpte"],
        default="scaffold",
        help=(
            "scaffold: Multi-pass LLM generation with auto file parsing (default). "
            "inline: Single prompt, single response. "
            "aider: Use Aider for repo-aware generation. "
            "gpte: Use GPT-Engineer for project scaffolding."
        ),
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Path to a prompt file (.md or .txt) or inline prompt string",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Ollama model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=5,
        help="Max generation passes for scaffold mode (default: 5)",
    )
    parser.add_argument(
        "--target-files",
        type=int,
        default=30,
        help="Target number of files before stopping (default: 30)",
    )
    parser.add_argument(
        "--api",
        choices=["ollama", "lmstudio", "openai"],
        default="ollama",
        help="API backend to use (default: ollama)",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Don't initialize git repo",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available Ollama models and exit",
    )
    parser.add_argument(
        "inline_prompt",
        nargs="*",
        help="Inline prompt (when --mode inline)",
    )

    args = parser.parse_args()

    # List models
    if args.list_models:
        list_models()
        return

    # Resolve prompt
    prompt = ""
    if args.prompt:
        prompt_path = Path(args.prompt)
        if prompt_path.exists():
            prompt = prompt_path.read_text(encoding="utf-8")
            print(f"  📝 Loaded prompt from {prompt_path} ({len(prompt)} chars)")
        else:
            prompt = args.prompt  # Treat as inline string
    elif args.inline_prompt:
        prompt = " ".join(args.inline_prompt)
    else:
        parser.error("Provide --prompt <file_or_text> or an inline prompt")

    if not prompt.strip():
        parser.error("Prompt is empty")

    # Execute based on mode
    if args.mode == "scaffold":
        generate_multipass(
            prompt=prompt,
            model=args.model,
            output_dir=args.output,
            max_passes=args.passes,
            target_files=args.target_files,
            api_mode=args.api,
            git_init=not args.no_git,
        )
    elif args.mode == "inline":
        print(f"\n  Generating with {args.model}...\n")
        raw = call_ollama(prompt=prompt, model=args.model)
        files = parse_multi_file_output(raw)
        if files:
            write_files(files, args.output, git_init=not args.no_git)
        else:
            print("\n  (No structured files detected — raw output above)")
    elif args.mode == "aider":
        run_aider_scaffold(prompt=prompt, model=args.model, output_dir=args.output)
    elif args.mode == "gpte":
        run_gpte_scaffold(prompt=prompt, output_dir=args.output)


# Required for textwrap in argparse
import textwrap  # noqa: E402

if __name__ == "__main__":
    main()
