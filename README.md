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
