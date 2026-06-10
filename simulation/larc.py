# ================================================================
# simulation/larc.py
# Original LARC — Algorithm 1 + eq.(6)(7)(8) from the paper.
#
# Static heuristic: caches at every on-path node when CAS >= delta.
# No learning, no trend awareness, no selective placement.
# ================================================================

from collections import defaultdict, OrderedDict

from core.metrics import Metrics
from core.cas     import compute_cas
from config.settings import (
    BETA_BASE, GAMMA_AGE, L_MAX, NUM_WARMUP
)


def run_larc(
    G,
    server: int,
    csz: int,
    paths: dict,
    rseq,
    cseq,
    delta: float,
) -> dict:
    """
    Simulate the original LARC caching scheme.

    Parameters
    ----------
    G       : networkx Graph (topology)
    server  : origin-server node ID
    csz     : cache size (number of content slots per node)
    paths   : pre-computed all-pairs shortest paths dict
    rseq    : sequence of requester node IDs
    cseq    : sequence of requested content IDs
    delta   : CAS admission threshold (from DELTA_BY_ALPHA)

    Returns
    -------
    dict of scalar metrics (CHR, Latency, PathStretch, LinkLoad_*)
    """
    cache = {n: OrderedDict() for n in G.nodes()}
    freq  = defaultdict(int)
    cass  = defaultdict(float)   # per-content CAS score
    aged  = defaultdict(int)     # last time-step the content CAS was aged
    cpct  = defaultdict(int)     # copy count of content across network
    m     = Metrics()

    # ── Inner helpers ─────────────────────────────────────────────

    def age_node(node: int, ri: int) -> None:
        """Apply eq.(8) CAS multiplicative decay to all cached content."""
        for c in list(cache[node]):
            k = max(1, ri - aged[c])
            cass[c] *= (GAMMA_AGE ** k)
            aged[c]  = ri

    def hit_update(c: int) -> None:
        """Apply eq.(7) CAS additive boost on a cache hit."""
        old      = cass[c]
        cass[c]  = old + (1 - old) * BETA_BASE

    def insert(node: int, c: int, sc: float, ri: int) -> None:
        cache[node][c] = True
        if sc > cass[c]:
            cass[c] = sc
        aged[c]  = ri
        cpct[c] += 1

    def evict(node: int, c: int) -> None:
        del cache[node][c]
        cpct[c] = max(0, cpct[c] - 1)

    def admit(
        node: int, c: int,
        cs_e: float, cs_s: float,
        d_tot: float, d_trav: float,
        fv: float, ri: int,
    ) -> None:
        """
        Attempt to admit content `c` at `node` using the LARC rule.
        Admission: if CAS >= delta when cache has space.
        Eviction : if CAS of new content beats the minimum stored CAS.
        """
        if c in cache[node] or cpct[c] >= L_MAX:
            return
        sc = compute_cas(max(cs_e, 0), cs_s, d_tot, d_trav, fv)
        if cs_e > 0:
            if sc >= delta:
                insert(node, c, sc, ri)
        elif cache[node]:
            cm = min(cache[node], key=lambda x: cass.get(x, 0.0))
            if sc >= cass.get(cm, 0.0):
                evict(node, cm)
                insert(node, c, sc, ri)

    # ── Main simulation loop ──────────────────────────────────────

    for ri, (rq, c) in enumerate(zip(rseq, cseq)):
        meas  = (ri >= NUM_WARMUP)
        freq[c] += 1
        fv    = freq[c]

        path  = paths[int(rq)][server]
        pl    = len(path)
        d_tot = pl - 1
        cs_s  = csz * pl
        found = False

        # On-path hit search
        for hop, node in enumerate(path):
            if node != server:
                age_node(node, ri)
            if c in cache[node]:
                hit_update(c)
                aged[c] = ri
                if meas:
                    m.hit(hop, pl)
                found = True
                break

        # Cache miss → leave-copy-down along every on-path node
        if not found:
            if meas:
                m.miss(pl)
            for hop, node in enumerate(path[:-1]):
                cs_e = csz - len(cache[node])
                admit(
                    node, c, cs_e, cs_s,
                    d_tot, max(d_tot - hop, 1),
                    fv, ri,
                )

    return m.result()
