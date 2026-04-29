<div align="center">



  # NOVA

  ### Modular AI Orchestrator

  <p>
    <strong>Calm.</strong>
    <strong>Precise.</strong>
    <strong>Futuristic.</strong>
    <strong>Modular.</strong>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Core-Orchestrator-effbff?style=for-the-badge&labelColor=f8fdff&color=dff7ff" alt="Core Orchestrator" />
    <img src="https://img.shields.io/badge/Status-Active-f3fcff?style=for-the-badge&labelColor=f8fdff&color=e6f9ff" alt="Status Active" />
    <img src="https://img.shields.io/badge/Tests-21%20Passing-edfbff?style=for-the-badge&labelColor=f8fdff&color=ddf5ff" alt="Tests Passing" />
  </p>

  <p>
    <img src="https://img.shields.io/badge/Style-White%20%2B%20Cyan-f6fdff?style=flat-square&labelColor=fbfeff&color=e8f8ff" alt="Style" />
    <img src="https://img.shields.io/badge/Identity-Honest%20Execution-f6fdff?style=flat-square&labelColor=fbfeff&color=e4f7ff" alt="Identity" />
    <img src="https://img.shields.io/badge/Architecture-Clean%20Layers-f6fdff?style=flat-square&labelColor=fbfeff&color=e2f5ff" alt="Architecture" />
    <img src="https://img.shields.io/badge/Python-3.11+-f6fdff?style=flat-square&labelColor=fbfeff&color=e8f8ff" alt="Python 3.11+" />
  </p>
</div>

***

> *Nova is built to feel like a real system, not a chatbot costume stretched over tangled code.*

## Interface

<table>
<tr>
<td width="52%" valign="top">

### What Nova is

Nova is a modular AI orchestrator built around **routing, execution, memory, provider abstraction, and system identity**.

The idea is simple: separate the system into parts that can grow without collapsing into one giant unreadable loop.

This repo is trying to become a serious assistant architecture while keeping a strong visual and conceptual identity.

</td>
<td width="48%" valign="top">

### Design profile

```text
white surfaces
cyan glow
sterile lab atmosphere
calm android presence
clean system boundaries
honest execution
```

</td>
</tr>
</table>

***

## Signal lights

<p align="center">
  <img src="https://img.shields.io/badge/Agents-Ready-e8f8ff?style=for-the-badge&labelColor=f9feff&color=dff3ff" alt="Agents" />
  <img src="https://img.shields.io/badge/Execution-Wired-e8f8ff?style=for-the-badge&labelColor=f9feff&color=e5f7ff" alt="Execution" />
  <img src="https://img.shields.io/badge/Memory-Structured-e8f8ff?style=for-the-badge&labelColor=f9feff&color=e1f5ff" alt="Memory" />
  <img src="https://img.shields.io/badge/Providers-Abstracted-e8f8ff?style=for-the-badge&labelColor=f9feff&color=e8f8ff" alt="Providers" />
  <img src="https://img.shields.io/badge/Personality-Contained-e8f8ff?style=for-the-badge&labelColor=f9feff&color=dff6ff" alt="Personality" />
</p>

***

## Architecture map

```text
Nova
├── Agents         -> task-specific behavior
├── Orchestrator   -> turn handling and flow control
├── Execution      -> agent execution records and result safety
├── Registry       -> agent lookup and registration
├── Memory         -> storage and retrieval layers
├── Providers      -> model backend abstractions
└── Personality    -> identity scaffolding without contaminating core truth
```

<table>
<tr>
<th>Layer</th>
<th>Role</th>
<th>Why it matters</th>
</tr>
<tr>
<td><code>agents/</code></td>
<td>Specialized capabilities</td>
<td>Keeps behavior modular instead of hardcoding everything into one loop.</td>
</tr>
<tr>
<td><code>core/orchestrator.py</code></td>
<td>Turn routing</td>
<td>Lets Nova decide how to respond instead of blindly reacting.</td>
</tr>
<tr>
<td><code>core/execution.py</code></td>
<td>Execution service</td>
<td>Creates a real path for agent execution and result handling.</td>
</tr>
<tr>
<td><code>core/registry.py</code></td>
<td>Agent registry</td>
<td>Makes the system extensible without turning imports into chaos.</td>
</tr>
<tr>
<td><code>core/memory/</code></td>
<td>Memory layer</td>
<td>Gives Nova persistence and future continuity potential.</td>
</tr>
<tr>
<td><code>providers/</code></td>
<td>Model abstraction</td>
<td>Makes backend swaps possible without ripping the whole system apart.</td>
</tr>
</table>

***

## Current status

```bash
python -m pytest tests -q -s
# 21 passed in 0.04s
```

### Verified right now

- Package imports are fixed.
- The orchestrator path is working.
- Execution and registry schemas are aligned.
- Planner flow is passing under the current suite.
- The codebase is no longer in fake-working limbo.

***

## Quick start

<details>
<summary><strong>Linux / WSL setup</strong></summary>
<br>

```bash
git clone git@github.com:IVELINYTBG1/Nova_AI.git
cd Nova_AI
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests -q -s
```

</details>

<details>
<summary><strong>Windows PowerShell setup</strong></summary>
<br>

```powershell
git clone git@github.com:IVELINYTBG1/Nova_AI.git
cd Nova_AI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest tests -q -s
```

</details>

<details>
<summary><strong>What the repo is aiming for</strong></summary>
<br>

Nova is meant to evolve into a personal AI system with stronger planning, real providers, deeper memory, cleaner execution control, and a frontend/interface that actually matches the project identity.

The goal is not “just another assistant wrapper.” The goal is a system with real internal structure.

</details>

***

## Why Nova feels different

<table>
<tr>
<td width="50%" valign="top">

### Typical assistant projects

- One giant file.
- Memory bolted on later.
- Personality mixed into logic.
- Tools handled ad hoc.
- Hard to extend without breaking things.

</td>
<td width="50%" valign="top">

### Nova approach

- Separated layers.
- Execution tracked explicitly.
- Personality isolated from system truth.
- Providers abstracted.
- Built to scale without becoming sludge.

</td>
</tr>
</table>

***

## Principles

<div align="center">

| Principle | Meaning |
|---|---|
| **Honest execution** | Never claim an action succeeded when it did not. |
| **Clean boundaries** | Personality, execution, memory, and routing should not bleed into each other. |
| **Modular growth** | New agents and providers should plug in without wrecking the system. |
| **Strong identity** | The project should feel coherent in both code and presentation. |

</div>

***

## Roadmap

```text
[Phase 1] Stabilize core architecture        ██████████
[Phase 2] Replace provider stubs             ███░░░░░░░
[Phase 3] Deepen memory + orchestration      ██░░░░░░░░
[Phase 4] Add CI / branch protection         ██░░░░░░░░
[Phase 5] Real Nova interface layer          █░░░░░░░░░
```

<details>
<summary><strong>Expand roadmap</strong></summary>
<br>

### Near term

- Replace stub providers with actual model integrations.
- Improve planner behavior.
- Expand orchestrator logic.
- Improve memory retrieval quality.

### Mid term

- Add GitHub Actions for automated testing.
- Protect `main` and move to PR-first workflow.
- Clean repo hygiene and asset organization.

### Long term

- Build a real Nova runtime.
- Add richer multi-agent coordination.
- Create an interface layer that matches Nova’s visual identity.

</details>

***

## Repo pulse

```text
System state      : stable
Architecture      : modular
Visual identity   : established
Tests             : passing
Chaos level       : reduced
Potential         : high
```

***

## Final line

<div align="center">

## **Nova is not trying to be loud.**
### She is trying to be real.

</div><img width="1376" height="768" alt="generated-image" src="https://github.com/user-attachments/assets/ca0d8c26-9fa3-46c2-b12c-6d29402fa4a1" />
