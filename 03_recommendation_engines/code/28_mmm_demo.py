"""Module 28 — Marketing Mix Modeling demo.

Toy MMM with adstock decay + Hill-saturation curves. Synthesises ad spend,
generates sales, then recovers per-channel parameters via least-squares.

Run:  python 28_mmm_demo.py
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import minimize


def adstock(spend: np.ndarray, decay: float) -> np.ndarray:
    out = np.zeros_like(spend, dtype=float)
    carry = 0.0
    for t in range(len(spend)):
        carry = spend[t] + decay * carry
        out[t] = carry
    return out


def hill_saturation(x: np.ndarray, K: float, n: float) -> np.ndarray:
    return x ** n / (x ** n + K ** n)


def generate_data(n_weeks=104, seed=0):
    rng = np.random.default_rng(seed)
    # 3 channels: TV, Search, Social
    tv = rng.uniform(0, 100, n_weeks) + 50 * np.sin(np.arange(n_weeks) * 2 * np.pi / 52)
    search = rng.uniform(0, 50, n_weeks)
    social = rng.uniform(0, 30, n_weeks)

    # True params
    true_decays = [0.7, 0.3, 0.5]
    true_K = [40, 20, 15]
    true_n = [2.0, 1.5, 1.5]
    true_betas = [200, 150, 80]
    base = 500
    seasonality = 50 * np.sin(np.arange(n_weeks) * 2 * np.pi / 52)

    def channel_contrib(spend, decay, K, n, beta):
        return beta * hill_saturation(adstock(spend, decay), K, n)

    sales = base + seasonality
    sales += channel_contrib(tv, true_decays[0], true_K[0], true_n[0], true_betas[0])
    sales += channel_contrib(search, true_decays[1], true_K[1], true_n[1], true_betas[1])
    sales += channel_contrib(social, true_decays[2], true_K[2], true_n[2], true_betas[2])
    sales += rng.normal(0, 30, n_weeks)
    return tv, search, social, sales, dict(decays=true_decays, K=true_K, n=true_n, betas=true_betas, base=base)


def fit_mmm(channels, sales, n_weeks):
    """Joint fit of (decay, K, n, beta) per channel + intercept. Many params; for demo only."""
    n_channels = len(channels)
    seasonality = 50 * np.sin(np.arange(n_weeks) * 2 * np.pi / 52)
    sales_detrended = sales - seasonality

    def predict(params):
        out = np.full(n_weeks, params[0])  # base
        for c in range(n_channels):
            base_idx = 1 + c * 4
            decay, K, n, beta = params[base_idx:base_idx + 4]
            out = out + beta * hill_saturation(adstock(channels[c], decay), K, n)
        return out

    def loss(params):
        return float(np.mean((sales_detrended - predict(params)) ** 2))

    x0 = [400] + [0.5, 30, 1.5, 100] * n_channels
    bounds = [(0, 2000)] + [(0, 0.99), (1, 100), (0.5, 5), (0, 1000)] * n_channels
    result = minimize(loss, x0, method="L-BFGS-B", bounds=bounds)
    return result.x


def main():
    n_weeks = 104
    tv, search, social, sales, truth = generate_data(n_weeks=n_weeks)

    print("=== True parameters ===")
    print(f"  base: {truth['base']}")
    print(f"  decays: {truth['decays']}")
    print(f"  K: {truth['K']}")
    print(f"  n: {truth['n']}")
    print(f"  betas: {truth['betas']}")

    fitted = fit_mmm([tv, search, social], sales, n_weeks)
    print("\n=== Recovered ===")
    print(f"  base: {fitted[0]:.1f}")
    for c, name in enumerate(["TV", "Search", "Social"]):
        i = 1 + c * 4
        print(f"  {name:6s} decay={fitted[i]:.2f}  K={fitted[i + 1]:5.1f}  n={fitted[i + 2]:.2f}  beta={fitted[i + 3]:.1f}")


if __name__ == "__main__":
    main()
