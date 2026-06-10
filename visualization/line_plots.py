# ================================================================
# visualization/line_plots.py
# Line-chart figures (α=0.8 slice) showing QL advantage shading.
# ================================================================

import matplotlib.pyplot as plt

from config.settings import CACHE_PCT, RESULTS_DIR

# Per-scheme line styles
LS = {
    'LARC':             dict(color='#d62728', ls='--', marker='s', lw=1.8, ms=6),
    'Proposed LARC-QL': dict(color='#2ca02c', ls='-',  marker='o', lw=2.2, ms=6),
}


def plot_line(
    metric: str,
    cfg: dict,
    df,
    order: list,
    suffix: str = "",
    out_dir: str = RESULTS_DIR,
) -> None:
    """
    Save one PNG+PDF line figure across all topologies at α=0.8.
    A green shaded region highlights where LARC-QL outperforms LARC.

    Parameters
    ----------
    metric  : column name in df
    cfg     : dict with keys title, ylabel, better, best
    df      : pandas DataFrame of simulation results
    order   : list of topology names
    suffix  : optional filename suffix
    out_dir : directory to save figures into
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    fig.suptitle(
        f"{cfg['title']}  (α=0.8)",
        fontsize=12, fontweight='bold', y=1.01,
    )

    for ax, topo in zip(axes, order):
        td = df[(df['Topology'] == topo) & (df['Alpha'] == 0.8)]

        for sc, st in LS.items():
            sub = td[td['Scheme'] == sc].sort_values('CachePct')
            if sub.empty:
                continue
            ax.plot(
                sub['CachePct'], sub[metric],
                color=st['color'], ls=st['ls'],
                marker=st['marker'], lw=st['lw'],
                ms=st['ms'], label=sc,
            )
            last = sub.iloc[-1]
            ax.annotate(
                f"{last[metric]:.3f}",
                xy=(last['CachePct'], last[metric]),
                xytext=(4, 4), textcoords='offset points',
                fontsize=6.5, color=st['color'],
            )

        # Shade the QL-advantage region
        lv = (
            td[td['Scheme'] == 'LARC']
            .sort_values('CachePct')[metric]
            .values
        )
        qv = (
            td[td['Scheme'] == 'Proposed LARC-QL']
            .sort_values('CachePct')[metric]
            .values
        )
        xv = (
            td[td['Scheme'] == 'LARC']
            .sort_values('CachePct')['CachePct']
            .values
        )
        if len(lv) == len(qv) > 0:
            mask = (qv >= lv) if cfg['best'] == 'high' else (qv <= lv)
            ax.fill_between(
                xv, lv, qv, where=mask,
                alpha=0.15, color='#2ca02c',
                label='QL advantage',
            )

        ax.set_xticks(CACHE_PCT)
        ax.set_xticklabels(
            [f"{p:.2f}%" for p in CACHE_PCT],
            fontsize=7.5, rotation=20, ha='right',
        )
        ax.set_xlabel('Cache Size (% of total memory)', fontsize=8.5)
        ax.set_ylabel(cfg['ylabel'], fontsize=8.5)
        ax.set_title(topo, fontsize=10, fontweight='semibold')
        ax.legend(fontsize=7.5, loc='best', framealpha=0.85)
        ax.grid(linestyle=':', alpha=0.45)
        ax.text(
            0.98, 0.03, f"{cfg['better']} is better",
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=7, color='dimgray', style='italic',
        )

    plt.tight_layout()
    tag = metric.replace('LinkLoad_', 'LL_')
    fn  = f"{out_dir}/FINAL_line_{tag}{suffix}"
    plt.savefig(f"{fn}.png", bbox_inches='tight', dpi=150)
    plt.savefig(f"{fn}.pdf", bbox_inches='tight', dpi=150)
    plt.close()
    print(f"  Saved {fn}.png/.pdf")
