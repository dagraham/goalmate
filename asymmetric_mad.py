import numpy as np


def asymmetric_mad_bounds(intervals, mean_interval):
    """Compute separate MADs for positive and negative deviations."""
    positive_deviations = [x - mean_interval for x in intervals if x > mean_interval]
    negative_deviations = [mean_interval - x for x in intervals if x < mean_interval]

    mad_plus = np.mean(positive_deviations) if positive_deviations else 0
    mad_minus = np.mean(negative_deviations) if negative_deviations else 0

    n_plus = len(positive_deviations)
    n_minus = len(negative_deviations)

    return mad_plus, mad_minus, n_plus, n_minus


def chebyshev_asymmetric(intervals, mean_interval, eta_plus, eta_minus):
    """Compute asymmetric Chebyshev-like bounds."""
    mad_plus, mad_minus, n_plus, n_minus = asymmetric_mad_bounds(
        intervals, mean_interval
    )

    bound_plus = 1 - 1 / eta_plus**2 if eta_plus > 1 else 0
    bound_minus = 1 - 1 / eta_minus**2 if eta_minus > 1 else 0

    return {
        "upper_bound": mean_interval + eta_plus * mad_plus,
        "lower_bound": mean_interval - eta_minus * mad_minus,
        "prob_upper": bound_plus,
        "prob_lower": bound_minus,
    }


# Example Usage
intervals = [8, 10, 12, 14, 20, 22, 25]  # Sample intervals
mean_interval = np.mean(intervals)

# Choose different eta values for upper and lower deviations
# eta_plus, eta_minus = 2, 1.5
eta_plus, eta_minus = 2, 2

bounds = chebyshev_asymmetric(intervals, mean_interval, eta_plus, eta_minus)
print(bounds)
