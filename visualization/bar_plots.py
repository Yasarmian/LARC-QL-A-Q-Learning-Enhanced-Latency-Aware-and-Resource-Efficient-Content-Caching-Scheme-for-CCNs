# ================================================================
# visualization/bar_plots.py
# Bar-chart figures for each metric × topology × alpha combination.
# ================================================================

import numpy as np
import matplotlib.pyplot as plt

from config.settings import CACHE_PCT, RESULTS_DIR

# Shared style constants
COL = {'LARC': '#4878CF', 'Proposed LARC-QL': '#6ACC65'}
HAT = {'LARC': '',        'Proposed LARC-QL': '//'}
XL  = [f"{p:.2f}%" for p in CACHE_PCT]
XP  = np.arange(len(CACHE_PCT))
BW  = 0.35


def plot_bar(
    metric: str,
    cfg: dict,
    df,
    order: list,
    alpha_values: list,
    suffix: str = "",
    out_dir: str = RESULTS_DIR,
) -> None:
    """
    Save one PNG+PDF bar-chart figure per topology.

    Parameters
    ----------
    metric       : column name in df  (e.g. 'CHR')
    cfg          : dict with keys title, ylabel, better, best
    df           : pandas DataFrame of simulation results
    order        : list of topology names (determines subplot order)
    alpha_values : list of Zipf alpha values for subplots
    suffix       : optional filename suffix
    out_dir      : directory to save figures into
    """
    for topo in order:
        fig, axes = plt.subplots(1, 3, figsize=(15, 5.0))
        fig.suptitle(
            f"{cfg['title']} — {topo}",
            fontsize=12, fontweight='bold', y=1.03,
        )

        for ax, alpha in zip(axes, alpha_values):
            td = df[(df['Topology'] == topo) & (df['Alpha'] == alpha)]

            for bi, sc in enumerate(['LARC', 'Proposed LARC-QL']):
                sub = td[td['Scheme'] == sc].sort_values('CachePct')
                if sub.empty:
                    continue
                bars = ax.bar(
                    XP + (bi - 0.5) * BW,
                    sub[metric].values,
                    width=BW, color=COL[sc], hatch=HAT[sc],
                    label=sc, edgecolor='white', lw=0.5, alpha=0.88,
                )
                for bar, val in zip(bars, sub[metric].values):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() * 1.01,
                        f"{val:.3f}",
                        ha='center', va='bottom',
                        fontsize=5.5, rotation=90,
                        color=COL[sc],
                    )

            ax.set_xticks(XP)
            ax.set_xticklabels(XL, fontsize=7.5)
            ax.set_xlabel('Cache Size (% of total memory)', fontsize=8.5)
            ax.set_ylabel(cfg['ylabel'], fontsize=8.5)
            ax.set_title(f'α={alpha}', fontsize=10)
            ax.legend(fontsize=7.5, loc='best', framealpha=0.85)
            ax.grid(axis='y', linestyle=':', alpha=0.45)
            ax.text(
                0.02, 0.97, f"{cfg['better']} is better",
                transform=ax.transAxes,
                ha='left', va='top',
                fontsize=7, color='dimgray', style='italic',
            )

        plt.tight_layout()
        tag = metric.replace('LinkLoad_', 'LL_')
        fn  = f"{out_dir}/FINAL_{topo}_{tag}{suffix}"
        plt.savefig(f"{fn}.png", bbox_inches='tight', dpi=150)
        plt.savefig(f"{fn}.pdf", bbox_inches='tight', dpi=150)
        plt.close()
        print(f"  Saved {fn}.png/.pdf")
