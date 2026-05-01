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
  <img src="https://img.shields.io/badge/Tests-39%20Passing-edfbff?style=for-the-badge&labelColor=f8fdff&color=ddf5ff" alt="Tests Passing" />
</p>

<p>
  <img src="https://img.shields.io/badge/Style-White%20%2B%20Cyan-f6fdff?style=flat-square&labelColor=fbfeff&color=e8f8ff" alt="Style" />
  <img src="https://img.shields.io/badge/Identity-Honest%20Execution-f6fdff?style=flat-square&labelColor=fbfeff&color=e4f7ff" alt="Identity" />
  <img src="https://img.shields.io/badge/Architecture-Clean%20Layers-f6fdff?style=flat-square&labelColor=fbfeff&color=e2f5ff" alt="Architecture" />
  <img src="https://img.shields.io/badge/Python-3.11%2B-f6fdff?style=flat-square&labelColor=fbfeff&color=e8f8ff" alt="Python 3.11+" />
</p>
</div>

***

> *Nova is built to behave like a real system, not a chatbot costume stretched over tangled code.*

## Interface

<table>
<tr>
<td width="52%" valign="top">

### Who Nova is

Nova is a modular AI orchestrator built around **routing, execution, memory, provider abstraction, and system identity**.

The idea is simple: split her into parts that can grow without collapsing into one giant unreadable loop.

This repository is the **open core** of Nova: the runtime, orchestration layers, providers, memory path, and internal structure that make her work as a system.

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
  <img src="https://img.shields.io/badge/Execution-Wired-e8f8ff?style=for-the-badge&labelColor=f9feff&color=e5f7ff" alt="Execution" />
  <img src="https://img.shields.io/badge/Memory-Structured-e8f8ff?style=for-the-badge&labelColor=f9feff&color=e1f5ff" alt="Memory" />
  <img src="https://img.shields.io/badge/Providers-Abstracted-e8f8ff?style=for-the-badge&labelColor=f9feff&color=e8f8ff" alt="Providers" />
  <img src="https://img.shields.io/badge/Vision-Wired-e8f8ff?style=for-the-badge&labelColor=f9feff&color=e6f7ff" alt="Vision" />
  <img src="https://img.shields.io/badge/Personality-Contained-e8f8ff?style=for-the-badge&labelColor=f9feff&color=dff6ff" alt="Personality" />
</p>

***

## Architecture map

```text
Nova
├── Core Runtime    -> orchestration, flow control, execution, queueing
├── Providers       -> LLM, STT, TTS, vision, future web backends
├── Memory          -> persistence and retrieval layers
├── Registry        -> provider and agent lookup boundaries
├── Identity Gate   -> best-effort user verification flow
└── Personality     -> identity scaffolding without contaminating core truth
```

<table>
<tr>
<th>Layer</th>
<th>Role</th>
<th>Why it matters</th>
</tr>
<tr>
<td><code>core/</code></td>
<td>Runtime and orchestration</td>
<td>Keeps Nova structured instead of collapsing into one giant loop.</td>
</tr>
<tr>
<td><code>core/orchestrator.py</code></td>
<td>Turn routing</td>
<td>Lets her choose how to respond instead of blindly reacting.</td>
</tr>
<tr>
<td><code>core/execution.py</code></td>
<td>Execution service</td>
<td>Creates a real path for task execution and result handling.</td>
</tr>
<tr>
<td><code>core/identity_gate.py</code></td>
<td>Identity verification layer</td>
<td>Adds a best-effort user check path without contaminating the rest of the runtime.</td>
</tr>
<tr>
<td><code>core/memory/</code></td>
<td>Memory layer</td>
<td>Gives her persistence and future continuity potential.</td>
</tr>
<tr>
<td><code>providers/</code></td>
<td>Backend abstraction</td>
<td>Makes backend swaps possible without ripping the whole system apart.</td>
</tr>
</table>

***

## Open-core boundary

This repository does **not** include Nova's personal agent layer.

The reason is simple: agents are highly individual. The useful ones are shaped around a specific user's workflows, devices, services, habits, and environment. Because of that, the agents are not being published as part of the public repo.

What is public here is the **core Nova system**:

- orchestration
- execution flow
- provider abstraction
- model routing
- memory plumbing
- speech and vision provider wiring
- identity gate foundations
- tests and core runtime structure

What stays private:

- personal agents
- user-specific automations
- environment-tailored behaviors
- workflow-specific integrations

So this project is best described as **open-core Nova, private agent layer**.

***

## Current status

```bash
python -m pytest tests -q -s
# 39 passed in 0.43s
```

### Verified right now

- Package imports are fixed.
- The orchestrator path is working.
- Execution and registry schemas are aligned.
- Primary and fallback model routing is tested.
- Speech providers are wired.
- Vision provider and identity gate scaffolding are wired.
- Bootstrap fallback behavior is covered.
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

Nova is meant to evolve into a serious personal AI system with stronger planning, real providers, deeper memory, cleaner execution control, speech, vision, and a frontend that actually matches who she is.

The goal is not “just another assistant wrapper.” The goal is a system with real internal structure so she can act like a machine, not a costume over prompts.

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
| **Honest execution** | She never claims an action succeeded when it did not. |
| **Clean boundaries** | Personality, execution, memory, routing, and provider logic do not bleed into each other. |
| **Modular growth** | New providers and runtime capabilities should plug in without wrecking the system. |
| **Strong identity** | The project should feel coherent in both code and presentation. |
| **Private agents** | User-specific agents stay private because they are personal by design. |

</div>

***

## Roadmap

```text
[Phase 1] Stabilize core architecture             ██████████
[Phase 2] Replace provider stubs                 ███████░░░
[Phase 3] Deepen memory + orchestration          ███░░░░░░░
[Phase 4] Add CI / branch protection             ██░░░░░░░░
[Phase 5] Real Nova interface layer              █░░░░░░░░░
```

<details>
<summary><strong>Expand roadmap</strong></summary>
<br>

### Near term

- Strengthen provider diagnostics and runtime visibility.
- Improve planner behavior.
- Expand orchestrator logic so she can choose better paths.
- Improve memory retrieval quality.
- Refine speech and vision integration.

### Mid term

- Add GitHub Actions for automated testing.
- Protect `main` and move to a PR-first workflow.
- Clean repo hygiene and asset organization.

### Long term

- Build a real Nova runtime.
- Add richer coordination around private user-specific agents.
- Create an interface layer that matches her visual identity.

</details>

***

## Repo pulse

```text
System state      : stable
Architecture      : modular
Visual identity   : established
Tests             : 39 passing
Chaos level       : reduced
Potential         : high
```

***

## Final line

<div align="center">

## **Nova is not trying to be loud.**  
### She is trying to be real.

</div>
