# ================================================================
# visualization/linkload_plots.py
# Combined Internal + External link-load bar figure per topology.
# ================================================================

import numpy as np
import matplotlib.pyplot as plt

from config.settings import CACHE_PCT, RESULTS_DIR

XL = [f"{p:.2f}%" for p in CACHE_PCT]

# Colour palette: blue family = LARC, green family = LARC-QL
_C = {
    'LARC-Int': '#4878CF',
    'LARC-Ext': '#9BB5E8',
    'QL-Int':   '#3A9E45',
    'QL-Ext':   '#91D196',
}


def plot_linkload_combined(
    df,
    order: list,
    alpha_values: list,
    out_dir: str = RESULTS_DIR,
) -> None:
    """
    One figure per topology with three subplots (one per α value).
    Each subplot shows grouped bars:
        LARC-Internal | LARC-External | QL-Internal | QL-External

    Internal load = ICN-to-ICN  2 ms links.
    External load = ICN-to-server 34 ms links.
    """
    for topo in order:
        fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
        fig.suptitle(
            f"Link Load — Internal vs External — {topo}\n"
            f"(Internal: ICN↔ICN 2ms links | External: ICN↔Server 34ms links)",
            fontsize=11, fontweight='bold', y=1.04,
        )

        for ax, alpha in zip(axes, alpha_values):
            td = df[(df['Topology'] == topo) & (df['Alpha'] == alpha)]
            n  = len(CACHE_PCT)
            xp = np.arange(n)
            w  = 0.20   # width for four grouped bars per cache-size

            scheme_spec = [
                ('LARC',             'LinkLoad_Internal', 'LinkLoad_External',
                 _C['LARC-Int'], _C['LARC-Ext'], '', '//'),
                ('Proposed LARC-QL', 'LinkLoad_Internal', 'LinkLoad_External',
                 _C['QL-Int'],   _C['QL-Ext'],   '', '//'),
            ]

            for bi, (sc, int_key, ext_key, ci, ce, hi, he) in enumerate(scheme_spec):
                sub = td[td['Scheme'] == sc].sort_values('CachePct')
                if sub.empty:
                    continue
                offset_i = (bi * 2 - 1.5) * w
                offset_e = (bi * 2 - 0.5) * w

                bars_i = ax.bar(
                    xp + offset_i, sub[int_key].values,
                    width=w, color=ci, hatch=hi,
                    label=f"{sc[:4]} Internal",
                    edgecolor='white', lw=0.4, alpha=0.90,
                )
                bars_e = ax.bar(
                    xp + offset_e, sub[ext_key].values,
                    width=w, color=ce, hatch=he,
                    label=f"{sc[:4]} External",
                    edgecolor='white', lw=0.4, alpha=0.90,
                )

                for bar, val in zip(bars_i, sub[int_key].values):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.02,
                        f"{val:.2f}",
                        ha='center', va='bottom',
                        fontsize=4.8, rotation=90, color=ci,
                    )
                for bar, val in zip(bars_e, sub[ext_key].values):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.02,
                        f"{val:.2f}",
                        ha='center', va='bottom',
                        fontsize=4.8, rotation=90, color=ce,
                    )

            ax.set_xticks(xp)
            ax.set_xticklabels(XL, fontsize=7.5)
            ax.set_xlabel('Cache Size (% of total memory)', fontsize=8.5)
            ax.set_ylabel('Hops / Request', fontsize=8.5)
            ax.set_title(f'α={alpha}', fontsize=10)
            ax.legend(fontsize=6.5, loc='upper right', framealpha=0.85, ncol=2)
            ax.grid(axis='y', linestyle=':', alpha=0.40)
            ax.text(
                0.02, 0.97, '↓ lower is better',
                transform=ax.transAxes, ha='left', va='top',
                fontsize=7, color='dimgray', style='italic',
            )

        plt.tight_layout()
        fn = f"{out_dir}/FINAL_{topo}_LinkLoad_Combined"
        plt.savefig(f"{fn}.png", bbox_inches='tight', dpi=150)
        plt.savefig(f"{fn}.pdf", bbox_inches='tight', dpi=150)
        plt.close()
        print(f"  Saved {fn}.png/.pdf")
