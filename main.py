#!/usr/bin/env python3
# ================================================================
# main.py  —  LARC vs Proposed LARC-QL Simulation Runner
#
# Usage:
#   python main.py
#
# All tunable parameters live in config/settings.py.
# Results are written to:
#   outputs/LARC_LARCQL_FINAL.csv   ← raw numbers
#   results/FINAL_*.png / *.pdf     ← all figures
# ================================================================

import os
import random
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Project imports ───────────────────────────────────────────────
from config.settings import (
    ALPHA_VALUES, CACHE_PCT, DELTA_BY_ALPHA,
    NUM_CONTENTS, NUM_WARMUP, NUM_REQUESTS,
    TOPOLOGY_ORDER, OUTPUT_DIR, RESULTS_DIR,
    RANDOM_SEED,
)
from utils    import (
    create_topologies, get_server, precompute_paths,
    make_zipf, gen_requests, print_improvement_table,
)
from simulation import run_larc, run_larcql
from visualization import (
    plot_bar, plot_line, plot_linkload_combined, METRIC_CFG,
)


# ── Global matplotlib style ───────────────────────────────────────
mpl.rcParams.update({
    'font.family':       'DejaVu Sans',
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'axes.titlesize':    11,
    'axes.labelsize':    9,
    'xtick.labelsize':   8,
    'ytick.labelsize':   8,
    'legend.fontsize':   8,
})


def main():
    # ── Reproducibility ───────────────────────────────────────────
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # ── Output directories ────────────────────────────────────────
    os.makedirs(OUTPUT_DIR,  exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # ── Build topologies ──────────────────────────────────────────
    topos   = create_topologies()
    results = []

    # ── Simulation sweep ──────────────────────────────────────────
    for tn in TOPOLOGY_ORDER:
        G   = topos[tn]
        srv = get_server(G)
        print(f"\n{'=' * 65}")
        print(
            f"  {tn}  ({G.number_of_nodes()} nodes, "
            f"{G.number_of_edges()} edges,  SERVER=node {srv})"
        )
        print(f"{'=' * 65}")
        paths = precompute_paths(G)

        for alpha in ALPHA_VALUES:
            zp    = make_zipf(alpha)
            delta = DELTA_BY_ALPHA[alpha]
            print(f"\n  α={alpha}  δ={delta}")

            for cp in CACHE_PCT:
                csz           = max(1, int(cp / 100.0 * NUM_CONTENTS))
                total_reqs    = NUM_WARMUP + NUM_REQUESTS
                rseq, cseq    = gen_requests(G, srv, total_reqs, zp)

                # ── LARC ──────────────────────────────────────────
                rl = run_larc(G, srv, csz, paths, rseq, cseq, delta)
                rl.update(dict(
                    Scheme   = 'LARC',
                    Topology = tn,
                    CachePct = cp,
                    Alpha    = alpha,
                ))
                results.append(rl)

                # ── LARC-QL ───────────────────────────────────────
                rq = run_larcql(G, srv, csz, paths, rseq, cseq, zp, delta)
                rq.update(dict(
                    Scheme   = 'Proposed LARC-QL',
                    Topology = tn,
                    CachePct = cp,
                    Alpha    = alpha,
                ))
                results.append(rq)

                # ── Per-row console summary ────────────────────────
                def pct(new, old, up):
                    d = (new - old) / max(abs(old), 1e-9) * 100
                    return f"{d if up else -d:+.1f}%"

                print(
                    f"  {cp:.2f}%({csz:,})"
                    f"  LARC   [CHR={rl['CHR']:.4f}"
                    f" Lat={rl['Latency']:.2f}"
                    f" PS={rl['PathStretch']:.4f}"
                    f" LL_int={rl['LinkLoad_Internal']:.3f}"
                    f" LL_ext={rl['LinkLoad_External']:.3f}]"
                    f"\n          LARC-QL[CHR={rq['CHR']:.4f}"
                    f" Lat={rq['Latency']:.2f}"
                    f" PS={rq['PathStretch']:.4f}"
                    f" LL_int={rq['LinkLoad_Internal']:.3f}"
                    f" LL_ext={rq['LinkLoad_External']:.3f}]"
                    f"  ΔCHR={pct(rq['CHR'], rl['CHR'], True)}"
                    f" ΔLat={pct(rq['Latency'], rl['Latency'], False)}"
                    f" ΔLL_int={pct(rq['LinkLoad_Internal'], rl['LinkLoad_Internal'], False)}"
                    f" ΔLL_ext={pct(rq['LinkLoad_External'], rl['LinkLoad_External'], False)}"
                )

    # ── Save results CSV ──────────────────────────────────────────
    df       = pd.DataFrame(results)
    csv_path = f"{OUTPUT_DIR}/LARC_LARCQL_FINAL.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nSaved → {csv_path}")

    # ── Generate all plots ────────────────────────────────────────
    print("\nGenerating plots …")
    for metric, cfg in METRIC_CFG.items():
        plot_bar(metric, cfg, df, TOPOLOGY_ORDER, ALPHA_VALUES)
        plot_line(metric, cfg, df, TOPOLOGY_ORDER)

    plot_linkload_combined(df, TOPOLOGY_ORDER, ALPHA_VALUES)

    # ── Improvement summary table ─────────────────────────────────
    print_improvement_table(df, TOPOLOGY_ORDER, ALPHA_VALUES)


if __name__ == "__main__":
    main()
