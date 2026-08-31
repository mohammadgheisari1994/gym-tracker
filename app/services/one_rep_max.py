"""Estimated one-rep-max.

Uses the Epley formula: ``1RM = weight * (1 + reps / 30)``. See the
``brzycki-1993-1rm`` and ``lesuer-1997-1rm-accuracy`` entries in the reference
catalogue for the equations and their validation.
"""

from decimal import ROUND_HALF_UP, Decimal

_DIVISOR = Decimal(30)
_CENT = Decimal("0.1")


def epley_one_rep_max(weight: Decimal | None, reps: int) -> Decimal | None:
    """Return the Epley 1RM estimate, or ``None`` for a set with no weight."""
    if weight is None or reps < 1:
        return None
    estimate = Decimal(weight) * (1 + Decimal(reps) / _DIVISOR)
    return estimate.quantize(_CENT, rounding=ROUND_HALF_UP)
