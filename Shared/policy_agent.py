# shared/policy_agent.py

CARBON_PRICE = 0.14  # dollars per kg

def score(travel_time: float, co2_emissions: float, hov_bonus: float, ada_bonus: float) -> float:
    """
    Calculate cost score based on travel time, CO2 emissions, HOV lane use, and ADA support.

    Args:
        travel_time (float): Travel time in minutes
        co2_emissions (float): Estimated CO2 emissions in grams
        hov_bonus (float): HOV usage score
        ada_bonus (float): ADA support score

    Returns:
        float: Total cost score (lower is better)
    """
    return travel_time + co2_emissions * CARBON_PRICE - hov_bonus * 0.2 - ada_bonus * 0.1

def estimate_co2(travel_time: float, avg_load: float, k: float = 0.12) -> float:
    """
    Estimate CO2 emissions in grams.

    Args:
        travel_time (float): Travel time in minutes
        avg_load (float): Average number of passengers
        k (float): CO2 constant multiplier

    Returns:
        float: Estimated CO2 in grams
    """
    return k * travel_time * avg_load
