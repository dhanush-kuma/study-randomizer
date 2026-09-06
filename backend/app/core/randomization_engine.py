"""
randomization_engine.py
-----------------------
Pure-Python randomization algorithms for clinical-trial sequence generation.

All functions accept:
  arms      – list of dicts: [{"name": str, "short_code": str, "allocation_ratio": int}, ...]
  n         – total number of records to generate (target_sample_size)
  seed      – optional int/str seed for reproducibility
  kit_prefix– string prefix for auto-generated kit codes (e.g. "TRL001")

Each function returns a list of dicts:
  [{"sequence_number": int, "kit_code": str, "treatment_name": str}, ...]
"""

import random
import math


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_pool(arms: list[dict]) -> list[str]:
    """
    Expand arms into a flat pool according to their allocation_ratio.
    E.g. [{"name": "Drug", "allocation_ratio": 2}, {"name": "Placebo", "allocation_ratio": 1}]
    → ["Drug", "Drug", "Placebo"]
    """
    pool: list[str] = []
    for arm in arms:
        pool.extend([arm["name"]] * int(arm["allocation_ratio"]))
    return pool


def _kit_code(prefix: str, seq: int) -> str:
    """Generate a zero-padded kit code.  e.g. TRL001-0042"""
    return f"{prefix}-{seq:04d}"


def _int_seed(seed) -> int | None:
    """Coerce an arbitrary seed value to an integer (or None)."""
    if seed is None:
        return None
    try:
        return int(seed)
    except (ValueError, TypeError):
        return abs(hash(str(seed)))


# ---------------------------------------------------------------------------
# Algorithm 1 – Simple Random (weighted coin toss)
# ---------------------------------------------------------------------------

def simple_random(
    arms: list[dict],
    n: int,
    kit_prefix: str,
    seed=None,
) -> list[dict]:
    """
    Pure weighted random assignment.  Each of the n records is independently
    drawn from the arm pool with probability proportional to allocation_ratio.

    Pro:  simple, unbiased in the long run.
    Con:  can produce long runs of the same arm in small samples.
    """
    rng = random.Random(_int_seed(seed))
    pool = _build_pool(arms)

    records = []
    for i in range(1, n + 1):
        treatment = rng.choice(pool)
        records.append({
            "sequence_number": i,
            "kit_code": _kit_code(kit_prefix, i),
            "treatment_name": treatment,
        })
    return records


# ---------------------------------------------------------------------------
# Algorithm 2 – Permuted Block (fixed or variable)
# ---------------------------------------------------------------------------

def permuted_block(
    arms: list[dict],
    n: int,
    kit_prefix: str,
    block_size_min: int,
    block_size_max: int | None = None,
    seed=None,
) -> list[dict]:
    """
    Divides enrollment into balanced mini-blocks.  Within each block every arm
    appears proportionally (block_size must be a multiple of total_ratio).

    block_size_min == block_size_max  → fixed block size
    block_size_max > block_size_min   → variable block, randomly alternates

    If the requested block_size is not a multiple of total_ratio we round
    the block up to the nearest valid size automatically, then trim to n.
    """
    rng = random.Random(_int_seed(seed))
    total_ratio = sum(int(arm["allocation_ratio"]) for arm in arms)

    # Build candidate block sizes (must be multiples of total_ratio)
    if block_size_max is None or block_size_max <= block_size_min:
        # Fixed block
        raw_size = _round_up_to_multiple(block_size_min, total_ratio)
        block_sizes = [raw_size]
    else:
        # Variable block – collect all valid multiples in [min, max]
        block_sizes = _valid_block_sizes(block_size_min, block_size_max, total_ratio)
        if not block_sizes:
            # Fallback: nearest valid to min
            block_sizes = [_round_up_to_multiple(block_size_min, total_ratio)]

    sequence: list[str] = []

    while len(sequence) < n:
        block_size = rng.choice(block_sizes)
        # Build one proportionally-balanced block
        block: list[str] = []
        for arm in arms:
            copies = block_size * int(arm["allocation_ratio"]) // total_ratio
            block.extend([arm["name"]] * copies)
        rng.shuffle(block)
        sequence.extend(block)

    # Trim to exactly n
    sequence = sequence[:n]

    records = []
    for i, treatment in enumerate(sequence, start=1):
        records.append({
            "sequence_number": i,
            "kit_code": _kit_code(kit_prefix, i),
            "treatment_name": treatment,
        })
    return records


def _round_up_to_multiple(value: int, multiple: int) -> int:
    return math.ceil(value / multiple) * multiple


def _valid_block_sizes(min_size: int, max_size: int, multiple: int) -> list[int]:
    start = _round_up_to_multiple(min_size, multiple)
    return [s for s in range(start, max_size + 1, multiple)]


# ---------------------------------------------------------------------------
# Algorithm 3 – Minimization (adaptive balance approximation)
# ---------------------------------------------------------------------------

def minimization_approx(
    arms: list[dict],
    n: int,
    kit_prefix: str,
    seed=None,
    p_min: float = 0.80,
) -> list[dict]:
    """
    Pre-generation approximation of adaptive minimization.

    At each step we look at the current arm counts (weighted by allocation_ratio)
    and give a higher probability (p_min) to the most under-represented arm,
    spreading the remaining (1 - p_min) across the others.

    p_min (default 0.80) controls how aggressively the algorithm corrects
    imbalance – 0.5 degrades to simple random, 1.0 = pure deterministic.

    This is an honest approximation: real minimization acts at enrollment time
    using patient covariates; this pre-generates a sequence that dynamically
    self-balances without covariate data.
    """
    rng = random.Random(_int_seed(seed))
    total_ratio = sum(int(arm["allocation_ratio"]) for arm in arms)
    arm_names = [arm["name"] for arm in arms]
    arm_ratios = {arm["name"]: int(arm["allocation_ratio"]) for arm in arms}

    # Running counts
    counts = {name: 0 for name in arm_names}

    records = []
    for i in range(1, n + 1):
        # Compute "imbalance score" for each arm: how far below its target share?
        # target share = allocation_ratio / total_ratio
        total_assigned = sum(counts.values())

        if total_assigned == 0:
            # First record: pure weighted random
            pool = _build_pool(arms)
            chosen = rng.choice(pool)
        else:
            # Calculate expected vs actual for each arm
            deficit = {}
            for arm in arms:
                name = arm["name"]
                target_frac = arm_ratios[name] / total_ratio
                actual_frac = counts[name] / total_assigned
                deficit[name] = target_frac - actual_frac  # positive = under-represented

            max_deficit = max(deficit.values())
            most_needed = [name for name, d in deficit.items() if d == max_deficit]

            if len(most_needed) == 1:
                # One clear winner – apply p_min boost
                winner = most_needed[0]
                others = [name for name in arm_names if name != winner]

                probs = {}
                if others:
                    probs[winner] = p_min
                    each_other = (1.0 - p_min) / len(others)
                    for name in others:
                        probs[name] = each_other
                else:
                    probs[winner] = 1.0

                chosen = rng.choices(
                    population=list(probs.keys()),
                    weights=list(probs.values()),
                    k=1,
                )[0]
            else:
                # Tie – choose uniformly among tied arms
                chosen = rng.choice(most_needed)

        counts[chosen] += 1
        records.append({
            "sequence_number": i,
            "kit_code": _kit_code(kit_prefix, i),
            "treatment_name": chosen,
        })

    return records


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------

def generate_sequence(
    *,
    arms: list[dict],
    n: int,
    kit_prefix: str,
    method: str,
    block_size_min: int | None = None,
    block_size_max: int | None = None,
    seed=None,
) -> tuple[list[dict], int]:
    """
    Dispatch to the appropriate algorithm and return (records, seed_used).

    method: "Simple Random" | "Permuted Block" | "Minimization"
    """
    if not arms:
        raise ValueError("At least one treatment arm is required.")
    if n < 1:
        raise ValueError("Target sample size must be at least 1.")

    # Resolve / lock in the seed for auditability
    resolved_seed = _int_seed(seed) if seed is not None else random.randint(0, 2**31)

    if method == "Simple Random":
        records = simple_random(arms, n, kit_prefix, seed=resolved_seed)

    elif method == "Permuted Block":
        if block_size_min is None:
            raise ValueError("Block size (min) is required for Permuted Block randomization.")
        records = permuted_block(
            arms, n, kit_prefix,
            block_size_min=block_size_min,
            block_size_max=block_size_max,
            seed=resolved_seed,
        )

    elif method == "Minimization":
        records = minimization_approx(arms, n, kit_prefix, seed=resolved_seed)

    else:
        raise ValueError(f"Unknown randomization method: '{method}'")

    return records, resolved_seed
