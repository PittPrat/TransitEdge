def evaluate_policy(baseline, optimized):
    """
    Calculates percent improvement from baseline to optimized.
    Example: (50 - 35) / 50 = 0.30 = 30% improvement
    """
    return (baseline - optimized) / baseline

if __name__ == "__main__":
    baseline_tt = 50  # baseline travel time
    optimized_tt = 35  # optimized travel time after applying policy

    pct_improvement = evaluate_policy(baseline_tt, optimized_tt)
    print(f"Travel Time Improvement: {pct_improvement:.2%}") 