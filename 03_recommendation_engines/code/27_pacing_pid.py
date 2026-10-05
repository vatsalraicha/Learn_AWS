"""Module 27 — PID budget pacing controller demo.

Simulates a 24-hour campaign with hourly traffic; controller adjusts a bid
multiplier to track desired spend over time.

Run:  python 27_pacing_pid.py
"""
from __future__ import annotations
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def simulate(daily_budget=1000.0, kp=0.5, ki=0.05, kd=0.1, seed=0):
    rng = np.random.default_rng(seed)
    hours = np.arange(24)

    # Diurnal traffic curve — peaks evening
    traffic = 100 + 80 * np.sin((hours - 6) * np.pi / 12)
    traffic = np.maximum(traffic, 10)

    # Bid yield: each impression costs ~$0.5 base × bid_multiplier
    base_cost_per_impression = 0.5

    desired_spend_per_hour = daily_budget / 24
    cumulative_desired = np.cumsum(np.full(24, desired_spend_per_hour))

    spend = []
    multipliers = []
    integral = 0.0
    prev_error = 0.0
    actual_cum_spend = 0.0

    for t in hours:
        # PID
        error = (desired_spend_per_hour * (t + 1)) - actual_cum_spend
        integral += error
        # Anti-windup: clip integral
        integral = np.clip(integral, -daily_budget, daily_budget)
        derivative = error - prev_error
        multiplier = 1.0 + kp * error / daily_budget + ki * integral / daily_budget + kd * derivative / daily_budget
        multiplier = np.clip(multiplier, 0.1, 3.0)
        multipliers.append(multiplier)
        prev_error = error

        # Realised spend this hour
        imp_this_hour = traffic[t] * (multiplier / 2.0)  # multiplier influences win rate
        hour_spend = imp_this_hour * base_cost_per_impression * multiplier
        hour_spend += rng.normal(0, 5)  # noise
        hour_spend = max(0, hour_spend)
        spend.append(hour_spend)
        actual_cum_spend += hour_spend

    return hours, np.cumsum(spend), cumulative_desired, multipliers


def main():
    hours, actual, desired, mult = simulate(daily_budget=1000.0)

    print(f"Daily budget: $1000")
    print(f"Final spend: ${actual[-1]:.2f}")
    print(f"Hours with bid multiplier > 1.5: {sum(1 for m in mult if m > 1.5)}")
    print(f"Hours with bid multiplier < 0.5: {sum(1 for m in mult if m < 0.5)}")

    # Plot
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(hours, actual, label="Actual cumulative spend")
    axes[0].plot(hours, desired, label="Desired cumulative", linestyle="--")
    axes[0].set_ylabel("Cumulative spend ($)"); axes[0].legend(); axes[0].grid()
    axes[1].plot(hours, mult, color="orange")
    axes[1].set_ylabel("Bid multiplier"); axes[1].set_xlabel("Hour"); axes[1].grid()
    plt.suptitle("PID budget pacing — actual vs desired spend curve")
    out_path = "pacing_pid.png"
    plt.savefig(out_path); plt.close()
    print(f"\nPlot saved to {out_path}")


if __name__ == "__main__":
    main()
