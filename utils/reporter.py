# ================================================================
# utils/reporter.py
# Console improvement summary table: LARC-QL vs LARC per experiment.
# ================================================================

import pandas as pd
from config.settings import CACHE_PCT


def print_improvement_table(df, order: list, alpha_values: list) -> None:
    """
    Print a formatted improvement table to stdout.

    For each (topology, alpha, cache_size) combination, shows the
    relative improvement of LARC-QL over LARC for every metric.
    Positive values mean LARC-QL wins.
    """
    print(f"\n{'=' * 85}")
    print("LARC-QL vs LARC — IMPROVEMENT SUMMARY  (+ve = LARC-QL wins)")
    print(f"{'=' * 85}")

    def pct_up(new, old):
        """Higher-is-better improvement percentage."""
        return f"{(new - old) / max(abs(old), 1e-9) * 100:+.2f}%"

    def pct_dn(old, new):
        """Lower-is-better improvement percentage."""
        return f"{(old - new) / max(abs(old), 1e-9) * 100:+.2f}%"

    for topo in order:
        for alpha in alpha_values:
            td   = df[(df['Topology'] == topo) & (df['Alpha'] == alpha)]
            rows = []

            for cp in CACHE_PCT:
                lr = td[(td['Scheme'] == 'LARC') & (td['CachePct'] == cp)]
                qr = td[(td['Scheme'] == 'Proposed LARC-QL') & (td['CachePct'] == cp)]
                if lr.empty or qr.empty:
                    continue

                l = lr.iloc[0]
                q = qr.iloc[0]

                rows.append({
                    'Cache%'       : f"{cp:.2f}%",
                    'CHR↑'         : pct_up(q['CHR'],                l['CHR']),
                    'Latency↓'     : pct_dn(l['Latency'],            q['Latency']),
                    'PathStretch↓' : pct_dn(l['PathStretch'],        q['PathStretch']),
                    'LL_Int↓'      : pct_dn(l['LinkLoad_Internal'],  q['LinkLoad_Internal']),
                    'LL_Ext↓'      : pct_dn(l['LinkLoad_External'],  q['LinkLoad_External']),
                })

            if rows:
                print(f"\n  {topo}  α={alpha}")
                print(pd.DataFrame(rows).to_string(index=False))

    print("\nDone.")
