# visualization/__init__.py
from .bar_plots      import plot_bar
from .line_plots     import plot_line
from .linkload_plots import plot_linkload_combined

# ── Metric display configuration ─────────────────────────────────
# Each key is a DataFrame column name.
# title  : figure super-title
# ylabel : y-axis label
# better : direction annotation on the chart
# best   : 'high' or 'low'  (used for QL-advantage shading)

METRIC_CFG = {
    'CHR': dict(
        title  = 'Cache Hit Ratio (CHR)',
        ylabel = 'Hit Ratio',
        better = '↑',
        best   = 'high',
    ),
    'Latency': dict(
        title  = 'Average Latency (ms)',
        ylabel = 'Latency (ms)',
        better = '↓',
        best   = 'low',
    ),
    'PathStretch': dict(
        title  = 'Path Stretch',
        ylabel = 'Path Stretch',
        better = '↓',
        best   = 'low',
    ),
    'LinkLoad_Internal': dict(
        title  = 'Internal Link Load\n(ICN node ↔ ICN node, 2 ms links)',
        ylabel = 'Internal Hops / Request',
        better = '↓',
        best   = 'low',
    ),
    'LinkLoad_External': dict(
        title  = 'External Link Load\n(ICN node ↔ Server, 34 ms links)',
        ylabel = 'External Hops / Request',
        better = '↓',
        best   = 'low',
    ),
}
