# ================================================================
# core/cas.py
# Content Attractiveness Score — shared eq.(6) used by both schemes
# ================================================================

from config.settings import T_WINDOW


def compute_cas(
    cs_e: float,
    cs_s: float,
    d_tot: float,
    d_trav: float,
    fval: float,
) -> float:
    """
    Compute the Content Attractiveness Score (CAS) per paper eq.(6).

    Parameters
    ----------
    cs_e   : residual cache space at the candidate node
    cs_s   : total path cache capacity  (cache_size × path_length)
    d_tot  : total path distance in hops
    d_trav : distance already traversed by the interest packet
    fval   : cumulative request frequency for the content

    Returns
    -------
    float  : CAS value  (0.0 if inputs are degenerate)
    """
    if d_trav <= 0 or cs_s <= 0:
        return 0.0
    return (max(cs_e, 0) / (T_WINDOW * cs_s)) * (d_tot / d_trav) * fval
