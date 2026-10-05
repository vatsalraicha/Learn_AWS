"""Module 16 — Thompson sampling contextual bandit.

Compares Thompson sampling, ε-greedy, and pure greedy on a 10-arm Bernoulli bandit.
Run:  python bandit_thompson.py
"""
from __future__ import annotations
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def thompson_sampling(n_arms, true_means, n_steps, rng):
    alpha = np.ones(n_arms)
    beta = np.ones(n_arms)
    rewards = []
    for _ in range(n_steps):
        samples = rng.beta(alpha, beta)
        arm = int(np.argmax(samples))
        r = int(rng.random() < true_means[arm])
        alpha[arm] += r; beta[arm] += 1 - r
        rewards.append(r)
    return np.cumsum(rewards)


def epsilon_greedy(n_arms, true_means, n_steps, eps, rng):
    counts = np.zeros(n_arms)
    sums = np.zeros(n_arms)
    rewards = []
    for _ in range(n_steps):
        if rng.random() < eps:
            arm = rng.integers(0, n_arms)
        else:
            means = np.where(counts > 0, sums / np.maximum(counts, 1), 0.5)
            arm = int(np.argmax(means))
        r = int(rng.random() < true_means[arm])
        counts[arm] += 1; sums[arm] += r
        rewards.append(r)
    return np.cumsum(rewards)


def pure_greedy(n_arms, true_means, n_steps, rng):
    return epsilon_greedy(n_arms, true_means, n_steps, eps=0.0, rng=rng)


def main():
    rng = np.random.default_rng(0)
    true_means = rng.uniform(0.02, 0.20, size=10)
    print("True click-rates:", np.round(true_means, 3).tolist())
    print(f"Best arm true rate: {true_means.max():.3f}\n")

    n_steps = 5000
    rewards_ts  = thompson_sampling(10, true_means, n_steps, np.random.default_rng(1))
    rewards_eg  = epsilon_greedy(10, true_means, n_steps, eps=0.1, rng=np.random.default_rng(2))
    rewards_g   = pure_greedy(10, true_means, n_steps, np.random.default_rng(3))

    print(f"Cumulative reward after {n_steps} steps:")
    print(f"  Thompson:   {rewards_ts[-1]}")
    print(f"  ε-greedy:   {rewards_eg[-1]}")
    print(f"  pure greedy: {rewards_g[-1]}")
    print(f"  oracle:     {int(true_means.max() * n_steps)} (expected)")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(rewards_ts, label="Thompson sampling")
    ax.plot(rewards_eg, label="ε=0.1 greedy")
    ax.plot(rewards_g, label="pure greedy", linestyle="--")
    ax.plot(true_means.max() * np.arange(n_steps), label="oracle", color="black", linestyle=":")
    ax.set_xlabel("step"); ax.set_ylabel("cumulative reward"); ax.legend(); ax.grid()
    out_path = "bandit_comparison.png"
    plt.savefig(out_path); plt.close()
    print(f"\nPlot saved to {out_path}")


if __name__ == "__main__":
    main()
