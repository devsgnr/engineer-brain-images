"""Dependency-free binomial intervals and exact-test calculations.

Functions here operate only on counts. They do not classify tokens, select
conditions, load files or generate reports.
"""

import math

def wilson(k: int, n: int):
    """Return a pointwise Wilson 95% interval, or None for no observations."""
    if not n:
        return None
    z = 1.959963984540054
    p = k / n
    denominator = 1 + z*z/n
    centre = (p + z*z/(2*n)) / denominator
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denominator
    return [max(0., centre-half), min(1., centre+half)]


def _logcomb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return -math.inf
    return math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)


def fisher_greater(k1: int, n1: int, k0: int, n0: int) -> float:
    """One-sided Fisher exact test for a higher first-sample match proportion.

    The two rows are [noisy matches, noisy nonmatches] and [clean matches,
    clean nonmatches]. Sum the hypergeometric upper tail in log space to
    avoid overflowing large factorials. No changed predictions yields p=1
    for multiplicity correction, not an estimated conditional proportion.
    """
    if n1 == 0:
        return 1.
    total_successes = k1+k0
    total = n1+n0
    lo = max(0, n1-(total-total_successes))
    hi = min(n1, total_successes)
    logs = [_logcomb(total_successes, k)+_logcomb(total-total_successes, n1-k)-_logcomb(total, n1) for k in range(max(k1, lo), hi+1)]
    if not logs:
        return 0.
    pivot = max(logs)
    return min(1., math.exp(pivot)*sum(math.exp(x-pivot) for x in logs))


def adjust_holm(results: list, raw_key: str, adjusted_key: str) -> None:
    """Add Holm-adjusted p-values for one declared comparison family in place.

    Apply to all conditions, not only promising examples. Each annotation
    sensitivity analysis is a separate family. The shared clean sample and
    paired scaling seeds create dependence; Holm does not require independent
    tests. It does not repair retrospective choice of category definitions.
    """
    previous = 0.
    for rank, result in enumerate(sorted(results, key=lambda row: row[raw_key])):
        adjusted = min(1., max(previous, (len(results)-rank)*result[raw_key]))
        result[adjusted_key] = adjusted
        previous = adjusted
