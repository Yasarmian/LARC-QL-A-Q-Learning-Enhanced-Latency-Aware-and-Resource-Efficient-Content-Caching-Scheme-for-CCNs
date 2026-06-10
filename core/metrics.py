# ================================================================
# core/metrics.py
# Metrics accumulator — paper eq.(9), eq.(10), eq.(11)
# ================================================================

import numpy as np
from config.settings import INTERNAL_DELAY, EXTERNAL_DELAY


class Metrics:
    """
    Accumulates per-request statistics during the *measured* phase.

    Hit path  : only internal links are used (0 external hops).
    Miss path : internal hops  +  1 external hop to the origin server.
    """

    def __init__(self):
        self.hits      = 0
        self.misses    = 0
        self.lat       = 0.0      # total latency  (ms)
        self.ps        = []       # per-request path-stretch samples
        self.int_hops  = 0.0     # total internal link traversals
        self.ext_hops  = 0.0     # total external link traversals

    # ------------------------------------------------------------------
    def hit(self, hop: int, path_len: int):
        """Record a cache hit found at `hop` hops from the requester."""
        self.hits    += 1
        self.lat     += hop * INTERNAL_DELAY * 2            # eq.(9): req + data
        self.ps.append(hop / max(path_len - 1, 1))          # eq.(10)
        self.int_hops += max(hop, 1) * 2                    # both directions
        # No external link traversed on a hit
        self.ext_hops += 0

    # ------------------------------------------------------------------
    def miss(self, path_len: int):
        """Record a full cache miss (content fetched from origin server)."""
        ih = path_len - 1
        self.misses  += 1
        self.lat     += (ih * INTERNAL_DELAY + EXTERNAL_DELAY) * 2
        self.ps.append(1.0)
        self.int_hops += ih * 2   # both directions
        self.ext_hops += 1 * 2   # both directions

    # ------------------------------------------------------------------
    def result(self) -> dict:
        """Return a dict of scalar performance metrics."""
        total = self.hits + self.misses
        return dict(
            CHR               = self.hits      / max(total, 1),
            Latency           = self.lat       / max(total, 1),
            PathStretch       = float(np.mean(self.ps)) if self.ps else 1.0,
            LinkLoad_Internal = self.int_hops  / max(total, 1),
            LinkLoad_External = self.ext_hops  / max(total, 1),
        )
