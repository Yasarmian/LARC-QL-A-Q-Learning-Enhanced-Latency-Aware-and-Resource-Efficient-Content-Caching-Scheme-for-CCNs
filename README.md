# LARC vs Proposed LARC-QL — Simulation Project

Modular Python implementation of the **LARC** static caching heuristic and
the proposed **LARC-QL** Q-learning extension, evaluated across three
network topologies (GARR, GEANT, RocketFuel) and five cache-size settings.

---

## Project Structure

```
larc_project/
├── main.py                    ← Entry point — run this
├── requirements.txt
│
├── config/
│   ├── __init__.py
│   └── settings.py            ← ALL tunable parameters live here
│
├── core/
│   ├── __init__.py
│   ├── cas.py                 ← CAS formula (eq.6, shared by both schemes)
│   └── metrics.py             ← Metrics accumulator (CHR, Latency, etc.)
│
├── simulation/
│   ├── __init__.py
│   ├── larc.py                ← Original LARC algorithm
│   └── larcql.py              ← Proposed LARC-QL (Q-learning layer)
│
├── utils/
│   ├── __init__.py
│   ├── topology.py            ← Topology builders, Zipf, request generation
│   └── reporter.py            ← Console improvement summary table
│
├── visualization/
│   ├── __init__.py            ← METRIC_CFG display config
│   ├── bar_plots.py           ← Bar-chart figures per metric × topology
│   ├── line_plots.py          ← Line-chart figures (α=0.8 slice)
│   └── linkload_plots.py      ← Combined internal/external link-load figure
│
├── outputs/                   ← CSV results saved here (auto-created)
└── results/                   ← PNG/PDF plots saved here (auto-created)
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the simulation
```bash
python main.py
```

### 3. Outputs
| Path | Contents |
|------|----------|
| `outputs/LARC_LARCQL_FINAL.csv` | Raw per-experiment metrics |
| `results/FINAL_*.png / *.pdf`   | All bar, line, and link-load figures |

---

## Configuration

All parameters are in `config/settings.py`.  Key settings:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `NUM_CONTENTS` | 500 000 | Catalogue size |
| `NUM_WARMUP` | 300 000 | Q-table warm-up requests (not measured) |
| `NUM_REQUESTS` | 600 000 | Measured requests |
| `ALPHA_VALUES` | [0.6, 0.8, 1.0] | Zipf skew sweep |
| `CACHE_PCT` | [0.04 … 0.20] | Cache size sweep (% of catalogue) |
| `LR` | 0.20 | Q-learning rate |
| `GAMMA_Q` | 0.95 | Q-learning discount factor |
| `EPSILON` | 0.10 | ε-greedy exploration probability |
| `EWMA_FAST / SLOW` | 0.15 / 0.02 | Trend detection windows |
---

## Dataset

This project follows the standard **simulation-based evaluation methodology** widely adopted in Information-Centric Networking (ICN) and Content-Centric Networking (CCN) caching research. No external traffic trace dataset is used. Instead, request traces are synthetically generated using a **Zipf distribution**, which has been extensively validated for modeling real-world content popularity.

### Dataset Generation Parameters

| Parameter              | Value                                  |
| ---------------------- | -------------------------------------- |
| Content Catalogue Size | 500,000 content objects                |
| Zipf Parameters (α)    | {0.6, 0.8, 1.0}                        |
| Warm-up Requests       | 300,000 per configuration              |
| Measured Requests      | 600,000 per configuration              |
| Total Requests         | 900,000 per topology × α configuration |
| Network Topologies     | GARR, GEANT, RocketFuel                |

Since there are **3 network topologies** and **3 Zipf parameters**, the complete dataset contains:

**9 configurations × 900,000 requests = 8,100,000 total requests.**

### Dataset Files

| File                      |      Rows | Description                                                                                                                                                                                             |
| ------------------------- | --------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `requests_900k.csv`       | 8,100,000 | Complete request trace containing `request_id`, `phase`, `timestamp_ms`, `topology`, `alpha`, `content_id`, `content_rank`, `requester_node`, `path_length`, and `inter_arrival_ms`.                    |
| `raw_requests.csv`        |    18,000 | Sample per-request log containing topology, α, content rank, requester node, path length, inter-arrival time, and simulation phase (warm-up/measurement).                                               |
| `content_popularity.csv`  |    10,000 | Zipf probabilities, expected request counts, and normalized popularity values for all three α values.                                                                                                   |
| `simulation_trace.csv`    |     4,500 | Detailed simulation trace including EWMA fast/slow values, trend ratio (τ), CAS scores, adjusted CAS values, Q-table states, actions, rewards, cache hits/misses, latency, path stretch, and link load. |
| `performance_summary.csv` |       180 | Aggregated performance metrics including Cache Hit Ratio (CHR), latency, path stretch, and internal/external link loads for LARC and LARC-QL across all topology, α, and cache-size combinations.       |
| `qtable_states.csv`       |     2,520 | All Q1 and Q2 states with approximate converged Q-values for both actions and the preferred action label.                                                                                               |
| `ablation_results.csv`    |         7 | Results of the ablation study presented in the paper.                                                                                                                                                   |
| `ewma_trace.csv`          |     2,500 | EWMA fast and slow traces over 500 requests for content ranks 1, 2, 3, 10, and 100, corresponding to Figure 3 of the paper.                                                                             |

### Request Record Format

```text
request_id, phase, timestamp_ms, topology, alpha,
content_id, content_rank, requester_node,
path_length, cache_size_pct, inter_arrival_ms
```

### Reproducibility Statement

The synthetic request traces and benchmark topologies are generated to ensure controlled, reproducible, and fair comparisons between the original LARC scheme and the proposed LARC-QL approach. The use of Zipf-generated traces follows the same methodology adopted by prior ICN caching studies, enabling systematic evaluation under varying popularity skewness and cache-size conditions.

All datasets used to reproduce the experimental results reported in the paper are included in this repository.


---

## Why Q-Learning? (Design Notes)

LARC is a **static heuristic** — it uses a fixed CAS formula with fixed
parameters and cannot adapt to:

- Whether content popularity is **rising or falling right now**
- Whether a particular node's cache is under heavy pressure
- Whether caching at hop 1 vs hop 3 is better *for this content* given
  current demand patterns

**LARC-QL** adds two learned Q-tables:

- **Q1** — Miss-level gate: should we cache this content at all?
  - State: `(popularity_bin, avg_occupancy_bin, path_length_bin, trend_bin)`
  - LARC-QL learns *when not* to cache (e.g. falling-trend content wastes space)

- **Q2** — Hop-level gate: cache at this hop or not?
  - State: `(hop_bin, occupancy_at_node_bin, trend_bin)`
  - LARC-QL learns *which hop* is optimal — rising-trend content should be
    cached close to the requester; globally popular content closer mid-path

The **trend bin** (EWMA_fast / EWMA_slow ratio) is runtime information
that LARC's static formula cannot access, making the ML layer genuinely adaptive.



