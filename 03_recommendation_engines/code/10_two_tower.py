"""Module 10 — Two-tower retrieval with in-batch negatives + LogQ correction.

Run:  python 10_two_tower.py
"""
from __future__ import annotations
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class Tower(nn.Module):
    def __init__(self, vocab_size, emb_dim=32, hidden=64, out_dim=32):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim)
        self.mlp = nn.Sequential(
            nn.Linear(emb_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )

    def forward(self, idx):
        x = self.emb(idx)
        return F.normalize(self.mlp(x), dim=-1)


def train_step(user_tower, item_tower, user_idx, pos_item_idx, log_q, opt):
    u = user_tower(user_idx)              # (B, D)
    v = item_tower(pos_item_idx)          # (B, D)
    logits = u @ v.T                      # (B, B); diag = positive pairs
    logits = logits - log_q.unsqueeze(0)  # LogQ correction across columns
    labels = torch.arange(logits.size(0), device=logits.device)
    loss = F.cross_entropy(logits, labels)
    opt.zero_grad(); loss.backward(); opt.step()
    return loss.item()


def main():
    torch.manual_seed(0)
    n_users, n_items = 200, 1000
    emb_dim = 16
    batch_size = 64
    n_steps = 1000

    # Synthetic data: each user "prefers" items with item_id % 10 == user_id % 10
    def sample_batch():
        users = torch.randint(0, n_users, (batch_size,))
        pos_items = torch.tensor([
            ((users[i].item() % 10) + (torch.randint(0, n_items // 10, (1,)).item() * 10)) % n_items
            for i in range(batch_size)
        ])
        return users, pos_items

    # Item-frequency estimate (simple: uniform here, log_q = 0)
    log_q = torch.zeros(batch_size)

    user_tower = Tower(n_users, emb_dim=emb_dim, hidden=32, out_dim=emb_dim)
    item_tower = Tower(n_items, emb_dim=emb_dim, hidden=32, out_dim=emb_dim)
    opt = torch.optim.Adam(list(user_tower.parameters()) + list(item_tower.parameters()), lr=1e-3)

    for step in range(n_steps):
        users, pos = sample_batch()
        loss = train_step(user_tower, item_tower, users, pos, log_q, opt)
        if step % 200 == 0:
            print(f"step {step}  loss={loss:.4f}")

    # Build "ANN" by brute force; in production you'd use FAISS/HNSW
    with torch.no_grad():
        all_items = torch.arange(n_items)
        item_vecs = item_tower(all_items)   # (n_items, D)

        # Test: for user 7, top-10 should be heavy on items with id % 10 == 7
        u_idx = torch.tensor([7])
        u_vec = user_tower(u_idx)
        scores = (u_vec @ item_vecs.T).squeeze()
        top = torch.topk(scores, k=10).indices.tolist()
        print(f"\nuser 7 top-10 items: {top}")
        print(f"  of which item_id %% 10 == 7: {sum(1 for i in top if i % 10 == 7)}/10")


if __name__ == "__main__":
    main()
