"""Two small statistics helpers, written out so every number is explainable."""
from math import sqrt

from scipy.stats import binomtest


def wilson_ci(errors: int, n: int, z: float = 1.96):
    """95% Wilson confidence interval for a proportion.
    Better than the simple p +/- 1.96*SE when the rate is near 0% or 100%."""
    if n == 0:
        return (0.0, 0.0)
    p = errors / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, center - half), min(1.0, center + half))


def mcnemar_exact(a_wrong_b_right: int, a_right_b_wrong: int) -> float:
    """Paired test for two arms run on the SAME notes.
    Only notes where the arms disagree carry information. Under 'no difference'
    each disagreement is a coin flip, so we use an exact binomial test."""
    n = a_wrong_b_right + a_right_b_wrong
    if n == 0:
        return 1.0
    return binomtest(a_wrong_b_right, n, 0.5).pvalue
