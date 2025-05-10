def simulate_congestion(base_speeds):
    """
    Simulates congestion by reducing speed by 50% on segments 2, 4, and 5.

    Args:
        base_speeds (list of float): List of speeds per segment

    Returns:
        list of float: Modified speeds with congestion applied
    """
    return [speed * 0.5 if i in [2, 4, 5] else speed for i, speed in enumerate(base_speeds)]

def test_sim():
    before = [60, 60, 60, 60, 60, 60]
    after = simulate_congestion(before)
    assert after[2] == 30, f"Segment 2 failed: {after[2]}"
    assert after[4] == 30, f"Segment 4 failed: {after[4]}"
    assert after[5] == 30, f"Segment 5 failed: {after[5]}"
    print("Congestion simulation works")
    print("Before:", before)
    print("After:", after)


# Run test
if __name__ == "__main__":
    test_sim()
