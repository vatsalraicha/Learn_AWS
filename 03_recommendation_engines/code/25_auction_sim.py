"""Module 25 — Auction mechanism simulator.

Compares GSP, VCG, and first-price for a small slate of slots with
quality-adjusted ad ranks. Demonstrates incentive properties.

Run:  python 25_auction_sim.py
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass


@dataclass
class Bid:
    bidder: str
    bid_amount: float
    pCTR: float

    @property
    def ad_rank(self):
        return self.bid_amount * self.pCTR


def gsp_auction(bids: list[Bid], n_slots: int, slot_ctr_factors: list[float] | None = None):
    """Generalized Second Price: winner pays minimum bid to keep their position.

    With quality (pCTR), the price is set so the bidder's ad_rank just exceeds
    the next slot's ad_rank: price_i = ad_rank_{i+1} / pCTR_i.
    """
    sorted_bids = sorted(bids, key=lambda b: -b.ad_rank)
    if slot_ctr_factors is None:
        slot_ctr_factors = [1.0 / (i + 1) for i in range(n_slots)]
    results = []
    for slot in range(min(n_slots, len(sorted_bids))):
        winner = sorted_bids[slot]
        if slot + 1 < len(sorted_bids):
            next_rank = sorted_bids[slot + 1].ad_rank
            price = next_rank / winner.pCTR
        else:
            price = 0.01
        results.append((slot, winner.bidder, winner.bid_amount, price))
    return results


def vcg_auction(bids: list[Bid], n_slots: int, slot_ctr_factors: list[float] | None = None):
    """VCG: winner pays the externality they impose on others.

    Externality_i = welfare_others_without_i − welfare_others_with_i.
    """
    if slot_ctr_factors is None:
        slot_ctr_factors = [1.0 / (i + 1) for i in range(n_slots)]
    sorted_bids = sorted(bids, key=lambda b: -b.ad_rank)
    results = []
    for slot in range(min(n_slots, len(sorted_bids))):
        winner = sorted_bids[slot]
        others_with = [
            b.pCTR * b.bid_amount * slot_ctr_factors[s if s < slot else s - 1]
            for s, b in enumerate(sorted_bids) if b is not winner and s < n_slots
        ]
        # Without winner: everyone below moves up by one
        others_no_winner = sorted([b for b in bids if b is not winner], key=lambda b: -b.ad_rank)
        others_without = [
            b.pCTR * b.bid_amount * slot_ctr_factors[s]
            for s, b in enumerate(others_no_winner) if s < n_slots
        ]
        externality = sum(others_without) - sum(others_with)
        # VCG price for winner i = externality / winner_i_pCTR_normalized
        price = max(0, externality) / winner.pCTR
        results.append((slot, winner.bidder, winner.bid_amount, price))
    return results


def first_price_auction(bids: list[Bid], n_slots: int):
    """First-price: pay what you bid (per click)."""
    sorted_bids = sorted(bids, key=lambda b: -b.ad_rank)
    results = []
    for slot in range(min(n_slots, len(sorted_bids))):
        winner = sorted_bids[slot]
        results.append((slot, winner.bidder, winner.bid_amount, winner.bid_amount))
    return results


def main():
    bids = [
        Bid("Acme",   bid_amount=3.00, pCTR=0.04),
        Bid("Beta",   bid_amount=2.50, pCTR=0.06),
        Bid("Gamma",  bid_amount=2.00, pCTR=0.05),
        Bid("Delta",  bid_amount=1.50, pCTR=0.10),
        Bid("Epsilon", bid_amount=1.00, pCTR=0.03),
    ]
    n_slots = 3

    print("=== Bids (bid × pCTR = ad_rank) ===")
    for b in sorted(bids, key=lambda x: -x.ad_rank):
        print(f"  {b.bidder:8s}  bid=${b.bid_amount:.2f}  pCTR={b.pCTR:.3f}  ad_rank={b.ad_rank:.4f}")

    print("\n=== GSP ===")
    for slot, bidder, bid, price in gsp_auction(bids, n_slots):
        print(f"  slot {slot}: {bidder:8s} bids ${bid:.2f}, pays ${price:.2f}/click")

    print("\n=== VCG ===")
    for slot, bidder, bid, price in vcg_auction(bids, n_slots):
        print(f"  slot {slot}: {bidder:8s} bids ${bid:.2f}, pays ${price:.2f}/click")

    print("\n=== First-price ===")
    for slot, bidder, bid, price in first_price_auction(bids, n_slots):
        print(f"  slot {slot}: {bidder:8s} bids ${bid:.2f}, pays ${price:.2f}/click")

    print("\nNotes:")
    print("  GSP/VCG pay less than your bid (second-price family).")
    print("  First-price requires bid shading by the advertiser.")
    print("  pCTR matters: low-bid high-pCTR bidders can win slots over high-bid low-pCTR.")


if __name__ == "__main__":
    main()
