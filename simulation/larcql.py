# ================================================================
# simulation/larcql.py
# Proposed LARC-QL — LARC enhanced with a genuine Q-Learning layer.
#
# Two Q-tables replace static decisions in LARC:
#
#   Q1 — Miss-level gate:   CACHE this content or SKIP entirely?
#         State  = (pop_bin, avg_occ_bin, path_bin, trend_bin)
#         Action = 0:skip  /  1:proceed to hop-level decisions
#
#   Q2 — Hop-level gate:   cache at THIS specific hop or not?
#         State  = (hop_bin, occ_bin_at_node, trend_bin)
#         Action = 0:skip this node  /  1:cache here
#
# Content TREND (EWMA_fast / EWMA_slow):
#   Rising  → cache aggressively close to requester
#   Falling → skip or cache near server only
#   This runtime signal is completely unavailable to static LARC.
#
# Both Q-tables are trained online throughout the simulation.
# ================================================================

import math
import random
from collections import defaultdict, OrderedDict

from core.metrics import Metrics
from core.cas     import compute_cas
from config.settings import (
    BETA_BASE, GAMMA_AGE, L_MAX, NUM_WARMUP,
    LR, GAMMA_Q, EPSILON,
    POP_BINS, OCC_BINS, PATH_BINS, TREND_BINS, HOP_BINS,
    EWMA_FAST, EWMA_SLOW,
    BETA_POP_BONUS,
)


def run_larcql(
    G,
    server: int,
    csz: int,
    paths: dict,
    rseq,
    cseq,
    zp,
    delta: float,
) -> dict:
    """
    Simulate the proposed LARC-QL caching scheme.

    Parameters
    ----------
    G       : networkx Graph (topology)
    server  : origin-server node ID
    csz     : cache size (number of content slots per node)
    paths   : pre-computed all-pairs shortest paths dict
    rseq    : sequence of requester node IDs
    cseq    : sequence of requested content IDs
    zp      : Zipf probability array (used for popularity features)
    delta   : CAS admission threshold (from DELTA_BY_ALPHA)

    Returns
    -------
    dict of scalar metrics (CHR, Latency, PathStretch, LinkLoad_*)
    """
    nodes   = list(G.nodes())
    cache   = {n: OrderedDict() for n in nodes}
    freq    = defaultdict(int)
    cass    = defaultdict(float)
    aged    = defaultdict(int)
    cpct    = defaultdict(int)
    m       = Metrics()

    # ── Dual-EWMA trend tracking per content ─────────────────────
    ewf = defaultdict(float)   # fast EWMA  ≈ last  7 requests
    ews = defaultdict(float)   # slow EWMA  ≈ last 50 requests

    # ── Q-tables (lazy defaultdict — zero-initialised) ────────────
    Q1 = defaultdict(lambda: [0.0, 0.0])   # miss-level gate
    Q2 = defaultdict(lambda: [0.0, 0.0])   # hop-level gate

    maxp    = float(zp[0])   # max Zipf probability (rank-0 content)
    LOG_MAX = math.log1p(NUM_WARMUP + len(rseq))

    # ── Trend helpers ─────────────────────────────────────────────

    def update_trend(c: int) -> None:
        """Update EWMA trackers on every request for content c."""
        ewf[c] = EWMA_FAST * 1.0 + (1 - EWMA_FAST) * ewf[c]
        ews[c] = EWMA_SLOW * 1.0 + (1 - EWMA_SLOW) * ews[c]

    def get_trend_bin(c: int) -> int:
        """
        Classify demand trend into 3 bins.
        0 = falling  (fast < 90% of slow)
        1 = stable
        2 = rising   (fast > 110% of slow)
        """
        s = ews[c]
        if s < 1e-9:
            return 1
        r = ewf[c] / s
        if r > 1.10:
            return 2
        if r < 0.90:
            return 0
        return 1

    def trend_cas_factor(c: int) -> float:
        """
        Scale CAS by demand trend — a runtime signal LARC cannot use.
        Rising  → higher effective CAS (cache more aggressively)
        Falling → lower  effective CAS (evict sooner / admit less)
        """
        t = get_trend_bin(c)
        if t == 2:
            return 1.40
        if t == 0:
            return 0.65
        return 1.00

    # ── State encoders ────────────────────────────────────────────

    def pop_bin(c: int) -> int:
        return min(
            int(math.log1p(freq[c]) / LOG_MAX * POP_BINS),
            POP_BINS - 1,
        )

    def occ_bin(node: int) -> int:
        return min(
            int(len(cache[node]) / max(csz, 1) * OCC_BINS),
            OCC_BINS - 1,
        )

    def avg_occ_bin(path) -> int:
        vals = [
            len(cache[n]) / max(csz, 1)
            for n in path[:-1]
            if n in cache
        ]
        avg = sum(vals) / max(len(vals), 1)
        return min(int(avg * OCC_BINS), OCC_BINS - 1)

    def q1_state(c: int, path) -> tuple:
        return (
            pop_bin(c),
            avg_occ_bin(path),
            min(len(path) - 1, PATH_BINS - 1),
            get_trend_bin(c),
        )

    def q2_state(c: int, hop: int, node: int) -> tuple:
        return (min(hop, HOP_BINS - 1), occ_bin(node), get_trend_bin(c))

    # ── ε-greedy action selection ─────────────────────────────────

    def q1_act(s: tuple) -> int:
        if random.random() < EPSILON:
            return random.randint(0, 1)
        return 1 if Q1[s][1] >= Q1[s][0] else 0

    def q2_act(s: tuple) -> int:
        if random.random() < EPSILON:
            return random.randint(0, 1)
        return 1 if Q2[s][1] >= Q2[s][0] else 0

    # ── Bellman Q-table updates ───────────────────────────────────

    def q1_upd(s, a, r, ns):
        Q1[s][a] += LR * (r + GAMMA_Q * max(Q1[ns]) - Q1[s][a])

    def q2_upd(s, a, r, ns):
        Q2[s][a] += LR * (r + GAMMA_Q * max(Q2[ns]) - Q2[s][a])

    # ── CAS with trend factor (LARC-QL enhancement) ───────────────

    def cas_ql(c, cs_e, cs_s, d_tot, d_trav, fv) -> float:
        base = compute_cas(max(cs_e, 0), cs_s, d_tot, d_trav, fv)
        return base * trend_cas_factor(c)

    # ── Cache management helpers ──────────────────────────────────

    def hit_update(c: int) -> None:
        """eq.(7) with popularity-tiered beta multiplier."""
        pop   = min(float(zp[int(c)]) / max(maxp, 1e-12), 1.0)
        b     = BETA_BASE * (1 + BETA_POP_BONUS * pop)
        old   = cass[c]
        cass[c] = old + (1 - old) * b

    def age_node(node: int, ri: int) -> None:
        """Apply eq.(8) CAS decay to all content cached at node."""
        for c in list(cache[node]):
            k = max(1, ri - aged[c])
            cass[c] *= (GAMMA_AGE ** k)
            aged[c]  = ri

    def insert(node: int, c: int, sc: float, ri: int) -> None:
        cache[node][c] = True
        if sc > cass[c]:
            cass[c] = sc
        aged[c]  = ri
        cpct[c] += 1

    def evict(node: int, c: int) -> None:
        del cache[node][c]
        cpct[c] = max(0, cpct[c] - 1)

    def try_cache(
        node: int, c: int,
        cs_s: float, d_tot: float, d_trav: float,
        fv: float, ri: int,
    ) -> bool:
        """
        Attempt admission using LARC thresholds with trend-adjusted CAS.
        Returns True if the content was successfully admitted.
        """
        if c in cache[node] or cpct[c] >= L_MAX:
            return False
        cs_e = csz - len(cache[node])
        sc   = cas_ql(c, cs_e, cs_s, d_tot, d_trav, fv)
        if cs_e > 0:
            if sc >= delta:
                insert(node, c, sc, ri)
                return True
        elif cache[node]:
            cm = min(cache[node], key=lambda x: cass.get(x, 0.0))
            if sc >= cass.get(cm, 0.0):
                evict(node, cm)
                insert(node, c, sc, ri)
                return True
        return False

    # ── Main simulation loop ──────────────────────────────────────

    for ri, (rq, c) in enumerate(zip(rseq, cseq)):
        meas   = (ri >= NUM_WARMUP)
        freq[c] += 1
        fv     = freq[c]

        # Update EWMA trend on every request
        update_trend(c)

        path   = paths[int(rq)][server]
        pl     = len(path)
        d_tot  = pl - 1
        cs_s   = csz * pl
        found  = False
        tb     = get_trend_bin(c)
        pop    = float(zp[int(c)]) / max(maxp, 1e-12)

        # ── On-path hit search ────────────────────────────────────
        for hop, node in enumerate(path):
            if node != server:
                age_node(node, ri)
            if c in cache[node]:
                hit_update(c)
                aged[c] = ri
                if meas:
                    m.hit(hop, pl)

                # Q1 reward: past decision to cache paid off
                lat_saved = max(d_tot - hop, 0) * 2   # ms saved
                s1  = q1_state(c, path)
                ns1 = (
                    min(pop_bin(c) + 1, POP_BINS - 1),
                    avg_occ_bin(path),
                    min(pl - 1, PATH_BINS - 1),
                    tb,
                )
                q1_upd(s1, 1, 10.0 + lat_saved * 0.6, ns1)

                # Q2 reward: this hop was the right caching location
                s2  = q2_state(c, hop, node)
                ns2 = q2_state(c, max(0, hop - 1), node)
                q2_upd(s2, 1, 8.0 + lat_saved * 0.4, ns2)

                found = True
                break

        # ── Cache miss ────────────────────────────────────────────
        if not found:
            if meas:
                m.miss(pl)

            # Q1: should we cache this content at all?
            s1 = q1_state(c, path)
            a1 = q1_act(s1)

            if a1 == 1:
                # Q2: which hops should we cache at?
                cached_count  = 0
                best_hop_done = None

                for hop, node in enumerate(path[:-1]):
                    if hop == 0:
                        continue          # hop-0 is the requester itself
                    if cpct[c] >= L_MAX:
                        break

                    s2 = q2_state(c, hop, node)
                    a2 = q2_act(s2)

                    if a2 == 1:
                        ok = try_cache(
                            node, c, cs_s, d_tot,
                            max(d_tot - hop, 1), fv, ri,
                        )
                        if ok:
                            cached_count += 1
                            if best_hop_done is None:
                                best_hop_done = hop
                            prox_r  = 6.0 / max(hop, 1)
                            trend_r = (
                                3.0 if tb == 2 else
                               -1.0 if tb == 0 else
                                1.0
                            )
                            rw2 = prox_r + trend_r + pop * 4.0
                            q2_upd(
                                s2, 1, rw2,
                                q2_state(c, max(0, hop - 1), node),
                            )
                        else:
                            q2_upd(s2, 1, -1.5, s2)
                    else:
                        rw2 = -2.0 if tb == 2 else 0.5
                        q2_upd(s2, 0, rw2, s2)

                # Q1 update based on how many nodes actually admitted
                if cached_count > 0:
                    prox_r = 6.0 / max(best_hop_done, 1)
                    rw1 = prox_r + pop * 8.0 + (3.0 if tb == 2 else 0.0)
                else:
                    rw1 = -2.0
                q1_upd(s1, 1, rw1, q1_state(c, path))

            else:
                # Q1 chose SKIP
                if tb == 0:
                    rw1 = 1.0 + (1.0 - pop) * 2.0   # good: skip falling content
                else:
                    rw1 = -(pop * 8.0 + (4.0 if tb == 2 else 0.0))
                q1_upd(s1, 0, rw1, q1_state(c, path))

    return m.result()
