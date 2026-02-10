import numpy as np

def divide_number_randomly(total_number):
    # Generate 3 random numbers
    random_parts = np.random.rand(3)
    # Normalize them to sum to 1
    normalized_parts = random_parts / sum(random_parts)
    # Multiply by the total number
    result = normalized_parts * total_number
    return result


def biased_hbl_percentages(random_state=None, value: int=0):
    """
    Return (head_pct, body_pct, leg_pct) that sum to 100,
    biased so head > body > leg on average.
    """
    if random_state is None:
        random_state = np.random.RandomState()

    # Dirichlet parameters control the mean:
    # larger alpha -> more stable around that mean.
    # Example: mean ≈ [0.5, 0.35, 0.15]
    alpha = np.array([5.0, 3.5, 1.5])
    sample = random_state.dirichlet(alpha)  # sums to 1

    head_pct_base = round(sample[0] * 100, 2)
    body_pct_base = round(sample[1] * 100, 2)
    leg_pct_base  = round(100 - head_pct_base - body_pct_base, 2)

    head_pct = value*head_pct_base/100
    body_pct = value*body_pct_base/100
    leg_pct = value*leg_pct_base/100

    return head_pct, body_pct, leg_pct



