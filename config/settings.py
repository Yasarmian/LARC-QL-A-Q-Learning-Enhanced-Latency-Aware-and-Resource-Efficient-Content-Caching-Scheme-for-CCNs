# ================================================================
# config/settings.py
# Central configuration for LARC vs LARC-QL simulation
# Modify these values to change simulation behaviour.
# ================================================================

# ── Simulation scale ─────────────────────────────────────────────
NUM_CONTENTS   = 500_000     # total unique content items in catalog
NUM_WARMUP     = 300_000     # requests used to train Q-tables (not measured)
NUM_REQUESTS   = 600_000     # requests used for performance measurement

# ── Network delay model (milliseconds) ───────────────────────────
INTERNAL_DELAY = 2           # ms per hop between ICN nodes
EXTERNAL_DELAY = 34          # ms for the edge-node → origin server hop

# ── Experiment sweep axes ─────────────────────────────────────────
ALPHA_VALUES   = [0.6, 0.8, 1.0]         # Zipf skew parameters
CACHE_PCT      = [0.04, 0.08, 0.12,      # cache size as % of NUM_CONTENTS
                  0.16, 0.20]

# ── LARC baseline parameters (Table 2 of baseline paper) ─────────
BETA_BASE      = 0.30    # eq.(7): additive CAS boost on cache hit
GAMMA_AGE      = 0.90    # eq.(8): multiplicative CAS decay per time step
L_MAX          = 3       # max copies of the same content network-wide
T_WINDOW       = 100     # observation window for CAS eq.(6)

# DELTA thresholds per alpha:
# Chosen so that rank-500 content passes at alpha=0.6,
# rank-300 at alpha=0.8, rank-200 at alpha=1.0
DELTA_BY_ALPHA = {0.6: 0.04, 0.8: 0.09, 1.0: 0.15}

# ── LARC-QL (Q-learning) parameters ──────────────────────────────
LR             = 0.20    # Q-table learning rate
GAMMA_Q        = 0.95    # temporal discount factor
EPSILON        = 0.10    # ε-greedy exploration probability

# State-space discretisation bins
POP_BINS       = 10      # log-frequency popularity bins
OCC_BINS       = 5       # cache occupancy bins  (0=empty … 4=full)
PATH_BINS      = 8       # path-length bins
TREND_BINS     = 3       # 0=falling, 1=stable, 2=rising
HOP_BINS       = 8       # hop-distance bins

# Trend detection via dual EWMA
EWMA_FAST      = 0.15    # fast window  ≈ last  7 requests
EWMA_SLOW      = 0.02    # slow window  ≈ last 50 requests

# Popularity-tiered CAS boost multiplier (eq.7 enhancement)
BETA_POP_BONUS = 1.60

# ── Topology ordering (determines plot order) ─────────────────────
TOPOLOGY_ORDER = ['GARR', 'GEANT', 'RocketFuel']

# ── Output paths ─────────────────────────────────────────────────
OUTPUT_DIR     = "outputs"    # directory for saved CSV results
RESULTS_DIR    = "results"    # directory for saved plot images/PDFs

# ── Reproducibility ───────────────────────────────────────────────
RANDOM_SEED    = 42
