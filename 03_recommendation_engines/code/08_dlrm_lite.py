"""Module 8 — Tiny DLRM-style ranker.

Sparse features → embedding tables; dense features → bottom MLP; pairwise dot
products; top MLP → sigmoid. The actual production DLRM is the same shape with
much larger embedding tables.

Run:  python 08_dlrm_lite.py
"""
from __future__ import annotations
import torch
import torch.nn as nn


class DLRMLite(nn.Module):
    def __init__(self, sparse_field_dims, dense_dim, emb_dim=16, mlp_hidden=(64, 32)):
        super().__init__()
        self.emb = nn.ModuleList([nn.Embedding(n, emb_dim) for n in sparse_field_dims])
        self.bottom = nn.Sequential(
            nn.Linear(dense_dim, emb_dim), nn.ReLU(),
            nn.Linear(emb_dim, emb_dim), nn.ReLU(),
        )
        n_fields = len(sparse_field_dims) + 1     # sparse fields + 1 dense
        n_pairs = n_fields * (n_fields + 1) // 2  # upper-triangular (incl. diag)

        layers, prev = [], n_pairs + emb_dim
        for h in mlp_hidden:
            layers += [nn.Linear(prev, h), nn.ReLU()]
            prev = h
        layers += [nn.Linear(prev, 1)]
        self.top = nn.Sequential(*layers)

    def _interact(self, vectors):
        # vectors: (B, N, D)
        B, N, _ = vectors.shape
        T = torch.bmm(vectors, vectors.transpose(1, 2))   # (B, N, N) pairwise dot products
        idx = torch.triu_indices(N, N, offset=0)
        return T[:, idx[0], idx[1]]                       # (B, N*(N+1)/2)

    def forward(self, sparse_idx, dense_x):
        emb_vecs = [e(sparse_idx[:, k]) for k, e in enumerate(self.emb)]   # list of (B, D)
        d_vec = self.bottom(dense_x)                                       # (B, D)
        all_vecs = torch.stack(emb_vecs + [d_vec], dim=1)                  # (B, N, D)
        pair_feats = self._interact(all_vecs)                              # (B, N*(N+1)/2)
        x = torch.cat([d_vec, pair_feats], dim=1)
        return torch.sigmoid(self.top(x)).squeeze(-1)


def main():
    torch.manual_seed(0)
    sparse_field_dims = [1000, 500, 200]  # user_id, item_id, creator_id cardinalities
    dense_dim = 8
    model = DLRMLite(sparse_field_dims=sparse_field_dims, dense_dim=dense_dim)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    # Synthetic clicks: positive if (user_id + item_id) %% 7 == 0 (a learnable pattern)
    n_train = 5000
    sparse = torch.stack([
        torch.randint(0, sparse_field_dims[0], (n_train,)),
        torch.randint(0, sparse_field_dims[1], (n_train,)),
        torch.randint(0, sparse_field_dims[2], (n_train,)),
    ], dim=1)
    dense = torch.randn(n_train, dense_dim)
    labels = ((sparse[:, 0] + sparse[:, 1]) % 7 == 0).float()

    for epoch in range(50):
        idx = torch.randperm(n_train)
        for start in range(0, n_train, 256):
            b = idx[start:start + 256]
            logits = model(sparse[b], dense[b])
            loss = nn.functional.binary_cross_entropy(logits, labels[b])
            opt.zero_grad(); loss.backward(); opt.step()
        if epoch % 10 == 0:
            with torch.no_grad():
                preds = model(sparse, dense)
                acc = ((preds > 0.5).float() == labels).float().mean().item()
            print(f"epoch {epoch:3d}  loss={loss.item():.4f}  acc={acc:.3f}")

    # Test on novel (user, item) pairs
    with torch.no_grad():
        test_pos = torch.tensor([[0, 7, 5]])  # 0 + 7 = 7 % 7 == 0 → positive
        test_neg = torch.tensor([[0, 1, 5]])  # 0 + 1 = 1 % 7 != 0 → negative
        d = torch.zeros((1, dense_dim))
        print(f"\nP(click | known-positive pattern) = {model(test_pos, d).item():.3f}")
        print(f"P(click | known-negative pattern) = {model(test_neg, d).item():.3f}")


if __name__ == "__main__":
    main()
