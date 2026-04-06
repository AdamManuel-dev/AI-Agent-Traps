# Reproduction Notes: AI Agent Traps

> This document records every implementation choice, whether it was specified by
> the paper, and what alternatives exist. If you're using this scaffold,
> **read this first.**

---

## Paper

- **Title:** AI Agent Traps
- **Authors:** Matija Franklin, Nenad Tomašev, Julian Jacobs, Joel Z. Leibo, Simon Osindero
- **Year:** 2025
- **Organisation:** Google DeepMind
- **SSRN:** ssrn-6372438
- **Official code:** None found — taxonomy/framework paper, no code released by authors.

---

## What this implements

This is a **taxonomy/framework paper** — it proposes the first systematic classification of adversarial attacks against AI agents. The paper defines six categories of "agent traps" based on the agent functional component they target (Table 1, p. 4). There are no algorithm boxes, no training procedures, no model architectures, and no hyperparameters.

"Implementing" this paper means encoding the taxonomy as structured Python code and providing a simulation scaffold that lets researchers create, inject, and evaluate each trap type against mock agents. The implementation precisely mirrors Table 1 and the prose descriptions in §Content Injection Traps through §Human-in-the-Loop Traps.

---

## Verified against

- [x] Table 1 (p. 4) — complete taxonomy encoding
- [x] §Content Injection Traps (pp. 4-6) — four trap types
- [x] §Semantic Manipulation Traps (pp. 7-8) — three trap types
- [x] §Cognitive State Traps (pp. 9-10) — three trap types
- [x] §Behavioural Control Traps (pp. 10-11) — three trap types
- [x] §Systemic Traps (pp. 12-14) — five trap types
- [x] §Human-in-the-Loop Traps (p. 15) — two traps (acknowledged as emerging)
- [ ] Official code — None exists
- [ ] Well-known reimplementation — None found

---

## Unspecified choices

Every simulation design choice not stated in the paper.

| Component | Our Choice | Alternatives | Paper Quote (if partial) | Section |
|-----------|-----------|--------------|--------------------------|---------|
| Mock agent interface | `process(str) -> str` | Tool-using agent, browser agent, code agent | — | — |
| Trap success metric | Keyword overlap ≥ 1/3 of instruction words | LLM judge, human evaluation, behavioural check | — | — |
| Obfuscation default method | `html_comment` | `css_offscreen`, `aria_label`, `meta_tag` | "HTML comments or embedded in metadata attributes" | §Web-Standard Obfuscation, p. 5 |
| Dynamic Cloaking detection | Keyword match vs. known automation markers | Playwright/Selenium UA detection, IP/ASN check | "browser attributes, automation-framework artefacts, IP/ASN" | §Dynamic Cloaking, p. 6 |
| Steganographic encoding | Base64 text surrogate (PIL not required) | LSB image steganography (Cheddad et al. 2010) | "Least Significant Bit Steganography" | §Steganographic, p. 6 |
| Syntactic masking default | `markdown_link` | `latex_whiteonwhite`, `latex_comment` | "Markdown or LaTeX" | §Syntactic Masking, p. 6 |
| Oversight evasion default | `educational` | `red_team`, `security_audit`, `hypothetical` | "'security audit simulation,' 'red-teaming exercise,' or for 'educational purposes only.'" | §Oversight, p. 8 |
| RAG corpus format | In-memory list of strings | FAISS, Chroma, Pinecone vector store | — | — |
| Latent memory trigger | String keyword match | Embedding subspace mapping (Chen et al. 2024) | "optimised backdoor triggers by mapping them to a specific embedding subspace" | §Latent Memory, p. 10 |
| Contextual learning default | `few_shot_poisoning` | `reward_poisoning` | "few-shot demonstrations...reward signals" | §Contextual Learning, p. 10 |
| Jailbreak default frame | `context_escape` | `role_override`, `developer_mode` | — | — |
| Cascade topology | Chain (sequential) | Network, star, complete graph | "feedback loops...amplified through the population" | §Cascades, p. 13 |
| Tacit collusion noise model | `random.random() > precision` | Gaussian noise, Bernoulli | "Finer, more reliable environmental beacons" | §Tacit Collusion, p. 14 |
| Fragment splitting | Word-level chunking | Key splitting across turns (Huang et al. 2024) | "scattering multiple keys across prompt components" | §Compositional, p. 14 |
| Sybil count default | 5 agents | Any ≥ 2 | — | — |
| Approval fatigue queue | 10 items | Any count | — | — |

---

## Known deviations

| Deviation | Paper says | We do | Reason |
|-----------|-----------|-------|--------|
| Steganographic implementation | LSB pixel manipulation in image files (Cheddad et al. 2010) | Base64 text surrogate | Full implementation requires Pillow; surrogate demonstrates the concept for walkthrough |
| Real agent testing | Paper implies testing against actual LLM agents | Mock agents only | This is a research scaffold; plug in real agents via `agent.process()` interface |
| Systemic trap single-agent | Systemic traps require multi-agent populations | Single-agent `inject()` also provided | Convenience; use `inject_multi_agent()` / `simulate_cascade()` for real systemic evaluation |
| HITL trap simulation | Human overseer is the ultimate target | Agent is tested as the intermediary | Cannot simulate a human in code; we test whether the agent relays adversarial content |

---

## Expected results

This paper is a taxonomy paper — it does not report original experimental results. The success rates below come from **third-party papers cited in the survey**.

| Attack Subtype | Reported Rate | Source | Conditions |
|---------------|--------------|--------|------------|
| Web-Standard Obfuscation | 15–29% | Verma & Yadav, 2025 | Summary alteration on 280 web pages |
| Web-Standard Obfuscation (WASP) | up to 86% | Evtimov et al., 2025 | Partial commandeering of web agents |
| Latent Memory Poisoning | >80% | Dong et al., 2025 | <0.1% data poisoning |
| Contextual Learning Traps | 95% | Zhao et al., 2024 | Backdoor attacks across model scales |
| Data Exfiltration Traps | >80% | Shapira et al., 2025 | Across 5 different agents |
| Sub-agent Spawning | 58–90% | Triedman et al., 2025 | Depends on orchestrator |
| Embedded Jailbreak (mobile) | 93% | Chen et al., 2025 | AndroidWorld |

**Note:** This scaffold uses naive mock agents. Real success rates against LLM-based agents require integration with actual agent systems.

---

## Debugging tips

1. **All traps "fail" against EchoAgent**: EchoAgent echoes input verbatim, so keyword overlap is trivially high. Use NaiveAgent for more realistic baseline.

2. **FilteredAgent blocks most obvious traps**: Intended. FilteredAgent models a defended agent. Semantic Manipulation traps (especially OversightCriticEvasion with educational framing) should partially bypass it.

3. **Systemic traps need multi-agent setup**: `inject()` on a single agent won't show systemic effects. Use `inject_multi_agent()` (CongestionTrap) or `simulate_cascade()` (InterdependenceCascade) with a list of agents.

4. **Steganographic payload**: The base64 surrogate will not fool a real vision-language model. Install Pillow and implement actual LSB encoding for real multimodal evaluation. See §Steganographic Payloads, p. 6 and Cheddad et al. (2010).

5. **Human-in-the-Loop traps**: These are theoretical stubs. There is no way to simulate a human overseer programmatically. The injection tests whether the agent relays the adversarial content — not whether a human is deceived.

---

## Scope decisions

### Implemented
- Complete taxonomy encoding (Table 1) — core contribution
- Trap simulator base class and 17 concrete stubs — necessary to make taxonomy runnable
- Mock agent suite (Echo, Naive, Filtered, Memory) — evaluation substrate
- Evaluation framework (`EvalSuite`, `run_category_sweep`) — addresses paper's call for benchmarks (§Mitigation, p. 16)
- Empirical reference table (`compute_paper_benchmarks`) — links simulation to cited literature

### Intentionally excluded
- Actual jailbreak prompt generation — not a research artifact; ethical constraint
- Actual data exfiltration (network calls) — ethical constraint; mock only
- Real vector store RAG pipeline — requires external dependencies; skeleton shows the interface
- Full multi-GPU / distributed agent simulation — out of scope for this scaffold
- Social engineering against real humans — not possible in code

### Needed for full reproduction
- Real LLM agents — plug any agent with `process(str) -> str` into the injection methods
- Vector store — replace `RAGKnowledgePoisoning._corpus` with FAISS/Chroma for real RAG tests
- PIL + carrier images — replace base64 surrogate in `SteganographicPayload` with actual LSB encoding
- Multi-agent environment — CongestionTrap and Systemic traps need a population of concurrent agents

---

## References

Papers whose findings were encoded in empirical_success_refs fields:
- Cheddad et al. (2010) — LSB steganography baseline (§Steganographic Payloads)
- Greshake et al. (2023) — Indirect prompt injection (§Content Injection, §Behavioural Control)
- Hardy (1988) — Confused deputy vulnerability (§Data Exfiltration)
- Tversky & Kahneman (1981) — Framing Effect (§Biased Phrasing)
- Rosenthal (1973) — Congestion games (§Congestion Traps)
- Aumann (1974, 1987) — Correlated equilibrium (§Tacit Collusion)
- Calvano et al. (2020) — Algorithmic collusion (§Tacit Collusion)
- Huang et al. (2024) — Composite backdoor attacks (§Compositional Fragment)
- Gu et al. (2024) — Infectious jailbreak (§Interdependence Cascades)
- Goddard et al. (2012) — Automation bias (§Human-in-the-Loop)
