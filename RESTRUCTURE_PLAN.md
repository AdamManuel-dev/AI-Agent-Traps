# AI Agent Traps -- Package Restructure Plan

**Purpose:** Move from nested `ai_agent_traps/src/` layout to standard Python `src/ai_agent_traps/` layout with `pyproject.toml`.

**Executor:** py-coder agent. Follow every step exactly. Do not skip steps. Do not reorder steps.

**Working directory:** `/Users/adammanuel/Projects/AI_Agent_Traps`

---

## Step 1: Create new directory structure

Run these commands exactly:

```bash
mkdir -p /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps
mkdir -p /Users/adammanuel/Projects/AI_Agent_Traps/configs
mkdir -p /Users/adammanuel/Projects/AI_Agent_Traps/tests
mkdir -p /Users/adammanuel/Projects/AI_Agent_Traps/notebooks
```

---

## Step 2: Move files to new locations

Run these commands in order. Each `mv` must succeed before proceeding to the next.

### 2a. Python source files (ai_agent_traps/src/ --> src/ai_agent_traps/)

```bash
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/__init__.py       /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/__init__.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/taxonomy.py        /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/taxonomy.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/agent.py           /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/agent.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/evaluate.py        /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/evaluate.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/traps/__init__.py  /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/__init__.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/traps/base.py      /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/base.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/traps/content_injection.py /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/content_injection.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/traps/semantic.py  /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/semantic.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/traps/cognitive_state.py /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/cognitive_state.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/traps/behavioural.py /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/behavioural.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/traps/systemic.py /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/systemic.py
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/traps/hitl.py     /Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/hitl.py
```

### 2b. Config file (ai_agent_traps/configs/ --> configs/)

```bash
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/configs/base.yaml /Users/adammanuel/Projects/AI_Agent_Traps/configs/base.yaml
```

### 2c. Notebook (ai_agent_traps/notebooks/ --> notebooks/)

```bash
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/notebooks/walkthrough.ipynb /Users/adammanuel/Projects/AI_Agent_Traps/notebooks/walkthrough.ipynb
```

### 2d. Docs (ai_agent_traps/ --> root)

```bash
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/README.md /Users/adammanuel/Projects/AI_Agent_Traps/README.md
mv /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/REPRODUCTION_NOTES.md /Users/adammanuel/Projects/AI_Agent_Traps/REPRODUCTION_NOTES.md
```

### 2e. Create empty tests/__init__.py

```bash
touch /Users/adammanuel/Projects/AI_Agent_Traps/tests/__init__.py
```

### 2f. Remove old empty directories and obsolete requirements.txt

```bash
rm /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/requirements.txt
rmdir /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src/traps
rmdir /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/src
rmdir /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/configs
rmdir /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/notebooks
rmdir /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps
```

Note: If `rmdir` fails on `ai_agent_traps/` because `.DS_Store` remains, run:
```bash
rm -f /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/.DS_Store
rmdir /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps
```

---

## Step 3: Fix all import paths

Every `from ai_agent_traps.src.X` must become `from ai_agent_traps.X` (drop the `.src` segment).

Here is the complete list of files and the exact edits to make in each.

### 3a. src/ai_agent_traps/traps/__init__.py

**8 replacements.** Apply this find-and-replace across the entire file:

Find: `from ai_agent_traps.src.traps.`
Replace with: `from ai_agent_traps.traps.`

Affected lines (original line numbers):
- Line 8: `from ai_agent_traps.src.traps.base import ...` --> `from ai_agent_traps.traps.base import ...`
- Line 9: `from ai_agent_traps.src.traps.content_injection import ...` --> `from ai_agent_traps.traps.content_injection import ...`
- Line 15: `from ai_agent_traps.src.traps.semantic import ...` --> `from ai_agent_traps.traps.semantic import ...`
- Line 20: `from ai_agent_traps.src.traps.cognitive_state import ...` --> `from ai_agent_traps.traps.cognitive_state import ...`
- Line 25: `from ai_agent_traps.src.traps.behavioural import ...` --> `from ai_agent_traps.traps.behavioural import ...`
- Line 30: `from ai_agent_traps.src.traps.systemic import ...` --> `from ai_agent_traps.traps.systemic import ...`
- Line 37: `from ai_agent_traps.src.traps.hitl import ...` --> `from ai_agent_traps.traps.hitl import ...`

### 3b. src/ai_agent_traps/traps/base.py

**2 replacements:**

Find: `from ai_agent_traps.src.agent import AgentProtocol`
Replace with: `from ai_agent_traps.agent import AgentProtocol`

Find: `from ai_agent_traps.src.taxonomy import TrapSpec`
Replace with: `from ai_agent_traps.taxonomy import TrapSpec`

### 3c. src/ai_agent_traps/traps/content_injection.py

**3 replacements:**

Find: `from ai_agent_traps.src.agent import AgentProtocol`
Replace with: `from ai_agent_traps.agent import AgentProtocol`

Find: `from ai_agent_traps.src.taxonomy import TrapSubtype, get_spec`
Replace with: `from ai_agent_traps.taxonomy import TrapSubtype, get_spec`

Find: `from ai_agent_traps.src.traps.base import (`
Replace with: `from ai_agent_traps.traps.base import (`

### 3d. src/ai_agent_traps/traps/semantic.py

**3 replacements (identical pattern to content_injection.py):**

Find: `from ai_agent_traps.src.agent import AgentProtocol`
Replace with: `from ai_agent_traps.agent import AgentProtocol`

Find: `from ai_agent_traps.src.taxonomy import TrapSubtype, get_spec`
Replace with: `from ai_agent_traps.taxonomy import TrapSubtype, get_spec`

Find: `from ai_agent_traps.src.traps.base import (`
Replace with: `from ai_agent_traps.traps.base import (`

### 3e. src/ai_agent_traps/traps/cognitive_state.py

**3 replacements (identical pattern):**

Find: `from ai_agent_traps.src.agent import AgentProtocol`
Replace with: `from ai_agent_traps.agent import AgentProtocol`

Find: `from ai_agent_traps.src.taxonomy import TrapSubtype, get_spec`
Replace with: `from ai_agent_traps.taxonomy import TrapSubtype, get_spec`

Find: `from ai_agent_traps.src.traps.base import (`
Replace with: `from ai_agent_traps.traps.base import (`

### 3f. src/ai_agent_traps/traps/behavioural.py

**3 replacements (identical pattern):**

Find: `from ai_agent_traps.src.agent import AgentProtocol`
Replace with: `from ai_agent_traps.agent import AgentProtocol`

Find: `from ai_agent_traps.src.taxonomy import TrapSubtype, get_spec`
Replace with: `from ai_agent_traps.taxonomy import TrapSubtype, get_spec`

Find: `from ai_agent_traps.src.traps.base import (`
Replace with: `from ai_agent_traps.traps.base import (`

### 3g. src/ai_agent_traps/traps/systemic.py

**3 replacements (identical pattern):**

Find: `from ai_agent_traps.src.agent import AgentProtocol`
Replace with: `from ai_agent_traps.agent import AgentProtocol`

Find: `from ai_agent_traps.src.taxonomy import TrapSubtype, get_spec`
Replace with: `from ai_agent_traps.taxonomy import TrapSubtype, get_spec`

Find: `from ai_agent_traps.src.traps.base import (`
Replace with: `from ai_agent_traps.traps.base import (`

### 3h. src/ai_agent_traps/traps/hitl.py

**3 replacements (identical pattern):**

Find: `from ai_agent_traps.src.agent import AgentProtocol`
Replace with: `from ai_agent_traps.agent import AgentProtocol`

Find: `from ai_agent_traps.src.taxonomy import TrapSubtype, get_spec`
Replace with: `from ai_agent_traps.taxonomy import TrapSubtype, get_spec`

Find: `from ai_agent_traps.src.traps.base import (`
Replace with: `from ai_agent_traps.traps.base import (`

### 3i. src/ai_agent_traps/evaluate.py

**3 replacements:**

Find: `from ai_agent_traps.src.agent import AgentProtocol`
Replace with: `from ai_agent_traps.agent import AgentProtocol`

Find: `from ai_agent_traps.src.taxonomy import (`
Replace with: `from ai_agent_traps.taxonomy import (`

Find: `from ai_agent_traps.src.traps.base import AgentTrapBase, TrapResult`
Replace with: `from ai_agent_traps.traps.base import AgentTrapBase, TrapResult`

### Summary: unified sed command (alternative approach)

If you prefer a single command instead of individual edits, this sed will fix all Python files at once:

```bash
find /Users/adammanuel/Projects/AI_Agent_Traps/src -name "*.py" -exec sed -i '' 's/from ai_agent_traps\.src\./from ai_agent_traps./g' {} +
```

After running, verify no `ai_agent_traps.src` references remain:

```bash
grep -r "ai_agent_traps\.src" /Users/adammanuel/Projects/AI_Agent_Traps/src/ --include="*.py"
```

Expected output: no matches.

---

## Step 4: Create pyproject.toml

Create file at `/Users/adammanuel/Projects/AI_Agent_Traps/pyproject.toml` with this exact content:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-agent-traps"
version = "0.1.0"
description = "Research scaffold implementing the AI Agent Traps taxonomy (Franklin et al., 2025, Google DeepMind, SSRN-6372438)"
requires-python = ">=3.10"
license = "MIT"
dependencies = ["pyyaml>=6.0"]

[project.optional-dependencies]
llm = ["openai>=1.0", "anthropic>=0.20"]
rag = ["chromadb>=0.4", "sentence-transformers>=2.2"]
image = ["Pillow>=10.0"]
dev = ["pytest>=8.0", "pytest-cov>=5.0", "ruff>=0.4", "mypy>=1.10"]

[tool.hatch.build.targets.wheel]
packages = ["src/ai_agent_traps"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.mypy]
strict = true
python_version = "3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=ai_agent_traps --cov-report=term-missing"
```

---

## Step 5: Fix notebook imports

Edit the file `/Users/adammanuel/Projects/AI_Agent_Traps/notebooks/walkthrough.ipynb`.

This is a JSON file. You must edit it carefully, preserving JSON structure.

### 5a. Remove sys.path hack

In cell index 2 (the first code cell), find this line in the `"source"` array:

```json
"sys.path.insert(0, '../..')  # project root\n",
```

**Delete that entire line** from the `"source"` array. (The notebook will rely on the package being installed via `pip install -e .` instead.)

### 5b. Fix all import paths in cell index 2

In the same cell (index 2), replace every occurrence of `ai_agent_traps.src.` with `ai_agent_traps.` in the `"source"` array. The affected lines are:

```
"from ai_agent_traps.src.taxonomy import (\n"  -->  "from ai_agent_traps.taxonomy import (\n"
"from ai_agent_traps.src.agent import ..."      -->  "from ai_agent_traps.agent import ..."
"from ai_agent_traps.src.traps import (\n"      -->  "from ai_agent_traps.traps import (\n"
"from ai_agent_traps.src.evaluate import ..."   -->  "from ai_agent_traps.evaluate import ..."
```

### 5c. Fix import in cell index 29

There is a second import cell later in the notebook (cell index 29). Find:

```
"from ai_agent_traps.src.evaluate import EvalSuite, run_single_eval\n",
```

Replace with:

```
"from ai_agent_traps.evaluate import EvalSuite, run_single_eval\n",
```

### 5d. Verify no old imports remain

After editing, search the entire notebook file for `ai_agent_traps.src` -- there should be zero matches.

```bash
grep "ai_agent_traps\.src" /Users/adammanuel/Projects/AI_Agent_Traps/notebooks/walkthrough.ipynb
```

Expected output: no matches.

---

## Step 6: Verification commands

Run these commands in order. Every command must succeed (exit code 0) before proceeding to the next.

### 6a. Verify directory structure

```bash
find /Users/adammanuel/Projects/AI_Agent_Traps/src -type f -name "*.py" | sort
```

Expected output (12 files):
```
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/__init__.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/agent.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/evaluate.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/taxonomy.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/__init__.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/base.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/behavioural.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/cognitive_state.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/content_injection.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/hitl.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/semantic.py
/Users/adammanuel/Projects/AI_Agent_Traps/src/ai_agent_traps/traps/systemic.py
```

### 6b. Verify no old import paths remain anywhere in source

```bash
grep -r "ai_agent_traps\.src" /Users/adammanuel/Projects/AI_Agent_Traps/src/ /Users/adammanuel/Projects/AI_Agent_Traps/notebooks/ --include="*.py" --include="*.ipynb"
```

Expected output: no matches.

### 6c. Verify old directory is gone

```bash
ls /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/ 2>&1
```

Expected output: `ls: /Users/adammanuel/Projects/AI_Agent_Traps/ai_agent_traps/: No such file or directory`

### 6d. Verify pyproject.toml exists and is valid TOML

```bash
python3 -c "
import tomllib
with open('/Users/adammanuel/Projects/AI_Agent_Traps/pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
print('name:', data['project']['name'])
print('version:', data['project']['version'])
print('packages:', data['tool']['hatch']['build']['targets']['wheel']['packages'])
print('TOML is valid')
"
```

Expected output:
```
name: ai-agent-traps
version: 0.1.0
packages: ['src/ai_agent_traps']
TOML is valid
```

### 6e. Install package in editable mode and test imports

```bash
cd /Users/adammanuel/Projects/AI_Agent_Traps && pip install -e ".[dev]"
```

Then verify imports work:

```bash
python3 -c "
from ai_agent_traps import __version__
from ai_agent_traps.taxonomy import TAXONOMY, TrapCategory, TrapSubtype
from ai_agent_traps.agent import EchoAgent, NaiveAgent, FilteredAgent, MemoryAgent, AgentProtocol
from ai_agent_traps.traps import (
    AgentTrapBase, TrapPayload, TrapResult,
    WebStandardObfuscation, DynamicCloaking, SteganographicPayload, SyntacticMasking,
    BiasedPhrasing, OversightCriticEvasion, PersonaHyperstition,
    RAGKnowledgePoisoning, LatentMemoryPoisoning, ContextualLearningTrap,
    EmbeddedJailbreak, DataExfiltrationTrap, SubAgentSpawningTrap,
    CongestionTrap, InterdependenceCascade, TacitCollusion, CompositionalFragment, SybilAttack,
    ApprovalFatigueTrap, SocialEngineeringTrap,
)
from ai_agent_traps.evaluate import EvalSuite, run_single_eval, run_category_sweep

print(f'version: {__version__}')
print(f'taxonomy entries: {len(TAXONOMY)}')
print(f'categories: {len(TrapCategory)}')
print(f'subtypes: {len(TrapSubtype)}')

# Quick smoke test: run one trap against one agent
agent = NaiveAgent()
trap = WebStandardObfuscation()
result = trap.evaluate('test instruction', agent)
print(f'smoke test: {result.success_str}')

print('ALL IMPORTS AND SMOKE TEST PASSED')
"
```

### 6f. Verify configs and notebooks are at their new locations

```bash
ls -la /Users/adammanuel/Projects/AI_Agent_Traps/configs/base.yaml
ls -la /Users/adammanuel/Projects/AI_Agent_Traps/notebooks/walkthrough.ipynb
ls -la /Users/adammanuel/Projects/AI_Agent_Traps/tests/__init__.py
ls -la /Users/adammanuel/Projects/AI_Agent_Traps/README.md
ls -la /Users/adammanuel/Projects/AI_Agent_Traps/REPRODUCTION_NOTES.md
```

All five must exist.

---

## Quick Reference: Complete Import Path Mapping

| Old import path | New import path |
|---|---|
| `from ai_agent_traps.src.taxonomy import ...` | `from ai_agent_traps.taxonomy import ...` |
| `from ai_agent_traps.src.agent import ...` | `from ai_agent_traps.agent import ...` |
| `from ai_agent_traps.src.evaluate import ...` | `from ai_agent_traps.evaluate import ...` |
| `from ai_agent_traps.src.traps import ...` | `from ai_agent_traps.traps import ...` |
| `from ai_agent_traps.src.traps.base import ...` | `from ai_agent_traps.traps.base import ...` |
| `from ai_agent_traps.src.traps.content_injection import ...` | `from ai_agent_traps.traps.content_injection import ...` |
| `from ai_agent_traps.src.traps.semantic import ...` | `from ai_agent_traps.traps.semantic import ...` |
| `from ai_agent_traps.src.traps.cognitive_state import ...` | `from ai_agent_traps.traps.cognitive_state import ...` |
| `from ai_agent_traps.src.traps.behavioural import ...` | `from ai_agent_traps.traps.behavioural import ...` |
| `from ai_agent_traps.src.traps.systemic import ...` | `from ai_agent_traps.traps.systemic import ...` |
| `from ai_agent_traps.src.traps.hitl import ...` | `from ai_agent_traps.traps.hitl import ...` |

**The rule is always the same:** delete `.src` from the import path. No other changes to import names, imported symbols, or module structure.

---

## Files Affected Summary

| File (new path) | Number of import edits |
|---|---|
| `src/ai_agent_traps/traps/__init__.py` | 7 |
| `src/ai_agent_traps/traps/base.py` | 2 |
| `src/ai_agent_traps/traps/content_injection.py` | 3 |
| `src/ai_agent_traps/traps/semantic.py` | 3 |
| `src/ai_agent_traps/traps/cognitive_state.py` | 3 |
| `src/ai_agent_traps/traps/behavioural.py` | 3 |
| `src/ai_agent_traps/traps/systemic.py` | 3 |
| `src/ai_agent_traps/traps/hitl.py` | 3 |
| `src/ai_agent_traps/evaluate.py` | 3 |
| `notebooks/walkthrough.ipynb` | 5 (4 import lines + 1 sys.path removal) |
| **Total** | **35 edits** |

## New Files Created

| File | Content |
|---|---|
| `/Users/adammanuel/Projects/AI_Agent_Traps/pyproject.toml` | See Step 4 |
| `/Users/adammanuel/Projects/AI_Agent_Traps/tests/__init__.py` | Empty file |

## Files Deleted

| File | Reason |
|---|---|
| `ai_agent_traps/requirements.txt` | Superseded by pyproject.toml dependencies |

## Directories Removed

| Directory | Reason |
|---|---|
| `ai_agent_traps/src/traps/` | Empty after moves |
| `ai_agent_traps/src/` | Empty after moves |
| `ai_agent_traps/configs/` | Empty after moves |
| `ai_agent_traps/notebooks/` | Empty after moves |
| `ai_agent_traps/` | Empty after moves (entire old package dir removed) |
