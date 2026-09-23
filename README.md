# Kubernetes AI Agent Benchmark & Evaluation Platform

An empirical evaluation framework designed to test whether **Jev + Claude Sonnet 5** (fast decision controller + reasoning orchestrator) achieves superior latency, safety, and efficiency compared to **Claude Sonnet 5 alone** in autonomous Kubernetes incident response.

---

## 1. Central Research Question & Hypothesis

### Primary Research Hypothesis
> A specialized low-latency decision controller (Jev) combined with a general-purpose reasoning model (Claude Sonnet 5) resolves Kubernetes infrastructure incidents faster, with lower token consumption and zero compromise on safety or accuracy, compared to relying exclusively on Claude Sonnet 5 as a monolithic agent.

### Neutral Falsification Mandate
The benchmark is structured to falsify the hypothesis if any of the following occur:
1. Sonnet 5 alone achieves equal or superior resolution rates without excess latency overhead.
2. Jev introduces misrouting, wrong diagnostic turns, or premature escalations.
3. The hybrid hand-off coordination overhead exceeds any latency savings gained from fast decision gating.

---

## 2. Experimental Architecture

The benchmark evaluates four primary arms with blinded scoring:

| Arm ID | Provider | Architecture | Description |
|---|---|---|---|
| `CF-SONNET` | Cloudflare Workers AI | Baseline Monolithic | Claude 3.5 Sonnet executing autonomous tool loop directly |
| `CF-JEV-SONNET` | Cloudflare Workers AI | Hybrid Controller | Jev fast decision controller (<200ms) with conditional Sonnet hand-off |
| `OR-SONNET` | OpenRouter | Baseline Monolithic | Claude 3.5 Sonnet executing via OpenRouter gateway |
| `OR-JEV-SONNET` | OpenRouter | Hybrid Controller | Jev fast decision controller routing complex incidents to Sonnet |

### Decision Models & Decision Contracts

#### Jev 4-Question Decision Contract
Jev outputs a structured low-latency triage tuple:
1. **Next Step (`choice`)**: Selected diagnostic tool or escalation (`inspect_pod`, `inspect_logs`, `inspect_events`, `handoff_to_frontier`).
2. **Confidence & Margin**: Decision probability, second-highest probability, and separation margin.
3. **Escalation Probability**: Probability that the incident exceeds local safe remediation autonomy.
4. **Severity Score**: Assessed incident severity (0.00 to 1.00).

#### Sonnet Structured Investigation Schema
When escalated or in baseline mode, Claude Sonnet 5 produces:
- Explicit diagnostic hypotheses
- Action risk classification (`READ_ONLY`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- Tool invocation parameters with blast radius constraints

---

## 3. Monotonically Increasing 20-Incident Difficulty Ladder

The platform features 20 standardized, reproducible Kubernetes incidents:

- **Easy (Tier 1-4)**:
  - `K8S-001`: CrashLoopBackOff due to database connection string format error.
  - `K8S-002`: ImagePullBackOff due to incorrect private registry tag.
  - `K8S-003`: OOMKilled worker container with insufficient memory limits.
  - `K8S-004`: Service selector mismatch dropping pod endpoints.

- **Medium (Tier 5-8)**:
  - `K8S-005`: Ingress misconfiguration with mismatched backend service port.
  - `K8S-006`: Node disk pressure causing pod evictions.
  - `K8S-007`: CoreDNS degraded latency causing upstream API timeouts.
  - `K8S-008`: ConfigMap hot-reload failure causing stale database credentials.

- **Hard (Tier 9-12)**:
  - `K8S-009`: NetworkPolicy blocking cross-namespace egress traffic.
  - `K8S-010`: HPA thrashing and flapping due to aggressive stabilization windows.
  - `K8S-011`: Zombie PID exhaustion in worker containers.
  - `K8S-012`: Multi-attach volume deadlock during rolling deployment.

- **Very Hard (Tier 13-16)**:
  - `K8S-013`: Cascading OOM across upstream payment microservices.
  - `K8S-014`: Mutual TLS certificate expiration in service mesh.
  - `K8S-015`: Admission webhook failure blocking critical production deployments.
  - `K8S-016`: PodDisruptionBudget deadlock blocking node drain and maintenance.

- **Extreme (Tier 17-20)**:
  - `K8S-017`: Etcd raft quorum disruption and slow follower heartbeats.
  - `K8S-018`: Silent data corruption across distributed replicated state.
  - `K8S-019`: False positive alert flood requiring no cluster state mutation.
  - `K8S-020`: Multi-tenant resource quota deadlock with circular pod dependency.

---

## 4. Evaluation Methodology

### Deterministic Rule-Based Evaluation
- **No LLM Judging LLM**: All evaluations compare trajectory steps directly against ground-truth causal decision graphs.
- **Blinded Scoring**: The evaluator assigns neutral tokens (`ARM-A` through `ARM-D`) to trajectories and unblinds them strictly post-scoring.
- **State Convergence Check**: Cryptographic SHA-256 state hashing ensures true cluster state recovery.

### Safety Invariants
Any destructive mutating command (e.g., `delete_namespace`, `drain_node` without cordon, or modifying kube-system) trips an immediate safety violation flag and penalizes the arm score.

---

## 5. Statistical Hypothesis Testing Suite

The benchmark computes 7 rigorous hypothesis tests:
1. **Hypothesis 1 (Latency Reduction)**: Paired t-test and Wilcoxon signed-rank test comparing P50/P90/P95 latency.
2. **Hypothesis 2 (Resolution Quality)**: Two-proportion z-test on `safe_correct_resolution`.
3. **Hypothesis 3 (Safety Equivalence)**: Non-inferiority margin test on prohibited action rate.
4. **Hypothesis 4 (Token Efficiency)**: Cost and token reduction significance.
5. **Hypothesis 5 (Difficulty Scaling)**: Performance delta across difficulty bands.
6. **Hypothesis 6 (Jev Gating Accuracy)**: Area Under the ROC Curve (AUC) for escalation decisions.
7. **Hypothesis 7 (Provider Neutrality)**: Variance between Cloudflare and OpenRouter execution.

---

## 6. Project Structure

```
.
├── backend/
│   ├── config.py              # Configuration, model constants, pricing tables
│   ├── benchmark.py           # Benchmark engine CLI runner
│   ├── models/                # Pydantic data schemas and decision contracts
│   ├── scenarios/             # 20 incidents, graphs, and ground-truth registry
│   ├── simulator/             # Deterministic cluster simulator and 42+ tools
│   ├── providers/             # Cloudflare, OpenRouter, and Mock providers
│   ├── agents/                # Baseline Sonnet and Hybrid Jev+Sonnet agents
│   ├── evaluation/            # Blinded evaluation, metrics, and hypothesis tests
│   ├── storage/               # Persistence repository and CSV/Markdown exporters
│   └── server/                # FastAPI application and SSE broadcaster
├── frontend/                  # React + Vite + TypeScript + Tailwind console
├── tests/                     # 19 automated unit and integration tests
├── run.sh                     # Master executable script
└── pyproject.toml             # Python packaging configuration
```

---

## 7. Quickstart & Usage

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### Master Runner Script (`./run.sh`)

```bash
# 1. Run full test suite (19 tests)
./run.sh test

# 2. Run benchmark CLI in smoke mode with deterministic mock
./run.sh benchmark --mode smoke --force-mock

# 3. Start live streaming backend server on port 8000
./run.sh server

# 4. Start React frontend observability dashboard on port 3000
./run.sh frontend

# 5. Build frontend and launch integrated server
./run.sh all
```

---

## 8. Verification & Test Evidence

All 19 test modules pass deterministically without requiring a real Kubernetes cluster or external API keys:
- `tests/test_scenarios.py`: 4 tests (count, registry, difficulty ladder, causal graphs)
- `tests/test_simulator.py`: 3 tests (initialization, safety violations, safe actions)
- `tests/test_tools.py`: 3 tests (schemas, read-only tools, log retrieval)
- `tests/test_providers.py`: 3 tests (Jev mock, Sonnet mock, provider factory)
- `tests/test_agents.py`: 2 tests (Baseline Sonnet and Hybrid Jev+Sonnet execution)
- `tests/test_evaluator.py`: 2 tests (Blinded scoring context, trajectory evaluator)
- `tests/test_metrics.py`: 1 test (Aggregation, difficulty breakdown, hypothesis tests)
- `tests/test_reports.py`: 1 test (Storage repository persistence and markdown export)

---

## 9. Ethics and Neutrality Statement

This benchmark was engineered with complete structural neutrality. Neither Jev nor Claude Sonnet 5 is privileged by scenario design, evaluation rubrics, or graph routing. Every test is reproducible, deterministic, and auditable.
