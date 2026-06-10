# ================================================================
# utils/topology.py
# Network topology construction, path pre-computation, and
# request sequence generation.
# ================================================================

import numpy as np
import networkx as nx
from config.settings import (
    INTERNAL_DELAY, NUM_CONTENTS, RANDOM_SEED
)

# Shared content catalogue (created once at import time)
CONTENTS = np.arange(NUM_CONTENTS, dtype=np.int32)


# ------------------------------------------------------------------
# Topology builders
# ------------------------------------------------------------------

def _finalise(G: nx.Graph) -> None:
    """
    Add delay attributes to every edge and ensure the graph is
    connected by bridging any isolated components.
    """
    for u, v in G.edges():
        G[u][v]['delay'] = INTERNAL_DELAY
    if not nx.is_connected(G):
        comps = list(nx.connected_components(G))
        for i in range(len(comps) - 1):
            G.add_edge(
                min(comps[i]), min(comps[i + 1]),
                delay=INTERNAL_DELAY
            )


def create_topologies() -> dict:
    """
    Return a dict of {name: nx.Graph} for the three benchmark
    topologies used in the paper.

    GARR       — power-law cluster  (40  nodes)
    GEANT      — Watts–Strogatz     (22  nodes)
    RocketFuel — Barabási–Albert    (52  nodes)
    """
    topo = {}

    G = nx.powerlaw_cluster_graph(40, 3, 0.50, seed=RANDOM_SEED)
    _finalise(G)
    topo['GARR'] = G

    G = nx.watts_strogatz_graph(22, 4, 0.30, seed=RANDOM_SEED)
    _finalise(G)
    topo['GEANT'] = G

    G = nx.barabasi_albert_graph(52, 3, seed=RANDOM_SEED)
    _finalise(G)
    topo['RocketFuel'] = G

    return topo


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def get_server(G: nx.Graph) -> int:
    """
    Return the highest-degree node as the origin server.
    This ensures all request paths are at least 2 hops, so CAS > 0.
    """
    return max(G.degree(), key=lambda x: x[1])[0]


def precompute_paths(G: nx.Graph) -> dict:
    """
    Pre-compute all-pairs shortest paths (dict-of-dicts).
    Called once per topology to avoid repeated BFS during simulation.
    """
    return dict(nx.all_pairs_shortest_path(G))


def make_zipf(alpha: float) -> np.ndarray:
    """
    Build a normalised Zipf probability vector of length NUM_CONTENTS.
    P(i) ∝ 1 / (i+1)^alpha
    """
    w = np.array([1.0 / (i + 1) ** alpha for i in range(NUM_CONTENTS)])
    return w / w.sum()


def gen_requests(
    G: nx.Graph,
    server: int,
    n: int,
    zp: np.ndarray,
) -> tuple:
    """
    Generate `n` (requester_node, content_id) pairs.

    Requesters are drawn uniformly from all non-server nodes.
    Content IDs are drawn from the Zipf distribution `zp`.

    Returns
    -------
    (rseq, cseq) : two numpy arrays of length n
    """
    non_server_nodes = [nd for nd in G.nodes() if nd != server]
    rseq = np.random.choice(non_server_nodes, size=n)
    cseq = np.random.choice(CONTENTS, size=n, p=zp)
    return rseq, cseq
