# redteam-ai-stack

Local LLM setup for offensive security code generation on Windows 11.  
Runs a 14B uncensored coder model on your GPU, wired to tools that can scaffold entire project trees from a single prompt.

**Hardware tested on:** MSI Vector 16 HX AI — i7-255HX, RTX 5070 Ti 12GB, 32GB DDR5  
**Author:** [NuRichter](https://github.com/NuRichter)  
**Last updated:** May 2026

---

## What this actually is

A ready-to-clone repo that sets up:

1. An **abliterated Qwen2.5-Coder 14B** running locally via Ollama — no cloud, no API keys, no content filters
2. A custom **Modelfile** with an offensive security system prompt and 32K context
3. Three code generation tools (**Aider**, **GPT-Engineer**, **Cline**) all pointed at your local model
4. A Python orchestrator (`run_lab.py`) that parses multi-file LLM output and writes entire directory trees to disk — the closest thing to "generate 100 files in one command" you'll get with a 14B

The whole thing fits in 12GB VRAM at Q4_K_M quantization. No CPU offload, no compromises on speed.

---

## Why these specific models

There's no public Qwen2.5-Coder-14B fine-tuned on offensive security data. That model doesn't exist as of May 2026 — WhiteRabbitNeo moved their 14B+ models behind a commercial paywall (DeepHat/Kindo), and the academic cyber fine-tunes target Qwen3-32B or larger.

So the play is: take the best uncensored 14B coder and give it a good system prompt.

| Model | What | Size (Q4_K_M) | Get it |
|-------|------|---------------|--------|
| `huihui_ai/qwen2.5-coder-abliterate:14b` | Qwen2.5-Coder-14B with refusal vectors surgically removed | 9.0 GB | `ollama pull huihui_ai/qwen2.5-coder-abliterate:14b` |
| Josiefied-Qwen2.5-Coder-14B-abliterated-v1 | Same base + extra unalignment fine-tune. Lower refusal rate. | 8.99 GB | Download GGUF from [mradermacher on HF](https://huggingface.co/mradermacher/Josiefied-Qwen2.5-Coder-14B-Instruct-abliterated-v1-GGUF) |
| WhiteRabbitNeo 2.5 Qwen-7B | The only open-weight model actually trained on 1.7M cyber Q&A pairs | 4.7 GB | GGUF from [bartowski on HF](https://huggingface.co/bartowski/WhiteRabbitNeo-2.5-Qwen-2.5-Coder-7B-GGUF) |

Start with the huihui one. One command, works immediately. Upgrade to Josiefied later if you hit refusals.

---

## VRAM math

Your RTX 5070 Ti Laptop GPU has 12GB GDDR7 on a 192-bit bus. Here's what fits:

| Quant | Weights | Leftover for KV cache | Usable context |
|-------|---------|----------------------|----------------|
| Q3_K_M | 7.3 GB | ~3.5 GB | 32K+ |
| **Q4_K_M** | **9.0 GB** | **~2.5 GB** | **16K–24K** |
| Q5_K_M | 10.5 GB | ~0.8 GB | 4–8K, too tight |
| Q6_K+ | >12 GB | doesn't fit | — |

Q4_K_M is the only sensible pick. Enable KV cache quantization (`q8_0`) to stretch context to 32K when you need it.

Expected speed: **30–45 tok/s** generation, **400–700 tok/s** prompt eval. An Aider session generating 50 files takes roughly 3–5 minutes.

---

## Setup (step by step)

### 0. Prerequisites

You need these installed before anything else:

```
NVIDIA Driver R570+     (any GameReady/Studio from Jan 2026+)
Python 3.11+            winget install Python.Python.3.12
Git                     winget install Git.Git
Node.js 20+             winget install OpenJS.NodeJS.LTS
VSCode                  winget install Microsoft.VisualStudioCode
```

Verify your GPU is visible:

```powershell
nvidia-smi
# Should show RTX 5070 Ti, Driver 570.xx+, CUDA 12.8+
```

If `nvidia-smi` doesn't show your GPU, update the driver from [nvidia.com/drivers](https://www.nvidia.com/drivers) first. Nothing else will work without this.

### 1. Install runtimes

```powershell
# LM Studio — primary runtime, best Blackwell support
winget install LMStudio.LMStudio

# Ollama — for CLI/scripting and the Modelfile system
winget install Ollama.Ollama
```

After install, set these environment variables (PowerShell as Admin):

```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_FLASH_ATTENTION", "1", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_KV_CACHE_TYPE", "q8_0", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "1", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_MAX_LOADED_MODELS", "1", "User")
```

Restart your terminal after this.

**Why two runtimes?** LM Studio has better RTX 50-series support (ships CUDA 12.8 builds, less Blackwell breakage). Ollama has the custom Modelfile system and one-liner model pulls. Use LM Studio as the server, Ollama for the model management. They both expose OpenAI-compatible APIs.

### 2. Pull the model

```powershell
ollama pull huihui_ai/qwen2.5-coder-abliterate:14b
```

~9 GB download. Go get coffee.

### 3. Build the custom Modelfile

This is the important part. The Modelfile bakes in a 32K context window and the offensive security system prompt so every tool that connects to this model gets consistent behavior.

```powershell
ollama create qwen-cyber -f modelfiles/Modelfile.qwen-cyber
```

Test it:

```powershell
ollama run qwen-cyber "Write a Python async port scanner with banner grabbing. Code only."
```

If you get code back without a lecture about ethics, you're good.

### 4. Install the agent tools

```powershell
pip install aider-chat gpt-engineer httpx rich typer pyyaml psutil requests
```

Then set persistent env vars so GPT-Engineer knows where to find your model:

```powershell
# Add to your PowerShell profile ($PROFILE)
$env:OPENAI_API_BASE = "http://127.0.0.1:11434/v1"
$env:OPENAI_API_KEY = "ollama"
$env:MODEL_NAME = "qwen-cyber"
```

### 5. VSCode extensions

**Cline** (agentic coding, plans and creates files with approval):
- Install from Extensions marketplace
- Set provider to "OpenAI Compatible", base URL `http://127.0.0.1:11434/v1`, model `qwen-cyber`
- **Turn on "Use Compact Prompt"** in Cline settings — this is non-negotiable, the default prompt eats your entire context window on a 14B

**Continue.dev** (autocomplete + inline chat):
- Install from marketplace
- Copy `configs/continue-config.yaml` to `~/.continue/config.yaml`

### 6. Smoke test

```powershell
python tests/smoke_test.py
```

Checks GPU detection, Ollama connectivity, model availability, refusal rate, and tool installations. All green = ready.

---

## Or just run the automated setup

If you don't want to do any of that manually:

```powershell
python setup_redteam_stack.py
```

Runs all six stages in order: system check, runtime install, model pull, Modelfile build, agent install, config write, smoke test. Takes about 20 minutes depending on your download speed.

Use `--check` to only verify your system, `--skip-models` if you already have the model, `--stage N` to run a single stage.

---

## Generating projects

### Single prompt to full project tree

```powershell
python run_lab.py --mode scaffold --prompt prompts/examples/recon_toolkit.md --output ./recon-kit
```

Sends your prompt to the model, parses the `=== FILE: ... ===` delimiters in the output, creates all directories and files, and initializes a git repo. It loops automatically — if the model can't fit everything in one response (it can't, 8K output token limit), `run_lab.py` tracks which files exist and asks for the rest.

Default is 5 passes targeting 30 files. Override with `--passes 10 --target-files 100` if you want more.

### Aider (git-tracked iterative editing)

Best for expanding an existing repo or when you want auto-commits per change:

```powershell
python run_lab.py --mode aider --prompt "Add an LDAP enumeration module to scanners/" --output ./recon-kit
```

Or launch Aider directly:

```powershell
cd my-project
copy C:\RedTeamStack\configs\.aider.conf.yml .
copy C:\RedTeamStack\configs\.aider.model.settings.yml .
aider --model ollama_chat/qwen-cyber
```

### GPT-Engineer (one-shot scaffold)

```powershell
python run_lab.py --mode gpte --prompt prompts/examples/c2_framework.md --output ./c2-lite
```

### Cline (visual, in VSCode)

Open your project folder, open Cline sidebar, type what you want. It plans, shows you each change, you approve. Good for when you want to actually watch what's happening.

---

## Repo structure

```
redteam-ai-stack/
├── README.md
├── setup_redteam_stack.py          ← automated full install
├── run_lab.py                      ← multi-file generation orchestrator
├── modelfiles/
│   └── Modelfile.qwen-cyber        ← custom Ollama Modelfile
├── configs/
│   ├── .aider.conf.yml
│   ├── .aider.model.settings.yml
│   └── continue-config.yaml
├── prompts/
│   ├── system_redteam.md
│   └── examples/
│       ├── recon_toolkit.md
│       ├── c2_framework.md
│       └── exploit_suite.md
└── tests/
    └── smoke_test.py
```

---

## Known issues

**Ollama sometimes doesn't see the RTX 5070 Ti.** Logs show `Total VRAM: 0 B`. This is a recurring Blackwell detection bug — Ollama issues [#13163](https://github.com/ollama/ollama/issues/13163) and [#14960](https://github.com/ollama/ollama/issues/14960). Usually fixed within a point release. Workaround: use LM Studio as your server instead, or try `$env:CUDA_VISIBLE_DEVICES = "0"` before starting Ollama.

**Aider produces garbled edits.** Make sure `edit_format: whole` is set in `.aider.conf.yml`. Local 14B models can't reliably do diff-style editing — they hallucinate line numbers. Full-file rewrites are slower but actually work.

**Model still refuses some prompts.** The huihui abliteration catches ~90% of refusals. If you hit the remaining 10%, switch to the Josiefied variant (more aggressive abliteration, ~98% pass rate on offensive prompts). Or just rephrase — adding "for an authorized pentest engagement" sometimes nudges it.

**Slow generation (<15 tok/s).** Check that the model is fully GPU-offloaded (`ollama ps`, look at `size_vram`). Close browsers with hardware acceleration. Make sure the laptop is plugged in and on High Performance power plan: `powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c`.

**"100 files in one command" is aspirational.** The model outputs ~8K tokens per turn, which is maybe 10–15 small files. `run_lab.py` handles this by looping — it's still one command from your side, but internally it's 5–10 LLM calls. A 100-file scaffold takes 5–10 minutes. That's the honest number.

---

## What this is not

This is not a magic box that replaces knowing what you're doing. The model will happily generate code that looks right but doesn't compile, uses deprecated APIs, or has subtle bugs. Review everything. Test everything. The model is a fast first draft, not a finished product.

This is also not a substitute for actual security training. If you don't understand what a ROP chain is, generating one won't help you. Learn the fundamentals — the model amplifies skill, it doesn't create it.

---

## Legal

Everything here is for **authorized penetration testing, CTFs, bug bounty programs, and academic research only**. Using offensive tools against systems without explicit written permission is illegal under CFAA, UU ITE, and equivalent laws in most jurisdictions.

The abliterated models will generate whatever you ask for without refusing. That's the point. The responsibility for what you do with the output is entirely yours.

---

*NuRichter Workspace 2026*
