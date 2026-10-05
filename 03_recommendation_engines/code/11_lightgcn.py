"""Module 11 — Minimal LightGCN with sparse adjacency propagation.

Run:  python 11_lightgcn.py
"""
from __future__ import annotations
import torch
import torch.nn as nn
import scipy.sparse as sp
import numpy as np


def build_norm_adj(R: sp.csr_matrix):
    """Build symmetric normalized adjacency for the user-item bipartite graph.

    A = [[0, R],
         [Rᵀ, 0]]
    D = diag(degrees)
    Â = D^{-1/2} A D^{-1/2}
    """
    n_users, n_items = R.shape
    n = n_users + n_items
    A = sp.lil_matrix((n, n))
    A[:n_users, n_users:] = R
    A[n_users:, :n_users] = R.T
    A = A.tocsr()
    deg = np.array(A.sum(axis=1)).flatten()
    d_inv_sqrt = np.power(deg, -0.5, where=deg > 0)
    d_inv_sqrt[deg == 0] = 0
    D = sp.diags(d_inv_sqrt)
    A_hat = D @ A @ D
    return A_hat.tocoo()


def to_torch_sparse(A_coo):
    indices = torch.tensor(np.vstack([A_coo.row, A_coo.col]), dtype=torch.long)
    values = torch.tensor(A_coo.data, dtype=torch.float32)
    return torch.sparse_coo_tensor(indices, values, A_coo.shape).coalesce()


class LightGCN(nn.Module):
    def __init__(self, n_users, n_items, emb_dim=32, n_layers=3):
        super().__init__()
        self.n_users = n_users
        self.n_items = n_items
        self.user_emb = nn.Embedding(n_users, emb_dim)
        self.item_emb = nn.Embedding(n_items, emb_dim)
        nn.init.normal_(self.user_emb.weight, std=0.1)
        nn.init.normal_(self.item_emb.weight, std=0.1)
        self.n_layers = n_layers

    def propagate(self, A_hat):
        e0 = torch.cat([self.user_emb.weight, self.item_emb.weight], dim=0)
        embs = [e0]
        e = e0
        for _ in range(self.n_layers):
            e = torch.sparse.mm(A_hat, e)
            embs.append(e)
        final = torch.stack(embs, dim=0).mean(dim=0)
        u_emb, i_emb = final.split([self.n_users, self.n_items])
        return u_emb, i_emb


def bpr_loss(u_emb, i_emb, users, pos, neg):
    pos_score = (u_emb[users] * i_emb[pos]).sum(-1)
    neg_score = (u_emb[users] * i_emb[neg]).sum(-1)
    return -torch.nn.functional.logsigmoid(pos_score - neg_score).mean()


def main():
    torch.manual_seed(0)
    np.random.seed(0)
    n_users, n_items = 50, 100

    # Synthetic: each user likes items with item_id % 5 == user_id % 5
    rows, cols = [], []
    for u in range(n_users):
        taste = u % 5
        for offset in range(np.random.randint(3, 8)):
            i = (taste + offset * 5) % n_items
            rows.append(u); cols.append(i)
    R = sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n_users, n_items))
    A_hat = to_torch_sparse(build_norm_adj(R))

    model = LightGCN(n_users, n_items, emb_dim=32, n_layers=3)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2, weight_decay=1e-4)

    # Build positive list per user
    user_pos = {u: set(R.getrow(u).indices.tolist()) for u in range(n_users)}

    for epoch in range(200):
        u_emb, i_emb = model.propagate(A_hat)
        users = torch.randint(0, n_users, (256,))
        pos = torch.tensor([np.random.choice(list(user_pos[u.item()])) for u in users])
        neg = torch.tensor([
            (lambda u=u: next(j for j in np.random.permutation(n_items) if j not in user_pos[u.item()]))()
            for u in users
        ])
        loss = bpr_loss(u_emb, i_emb, users, pos, neg)
        opt.zero_grad(); loss.backward(); opt.step()
        if epoch % 50 == 0:
            print(f"epoch {epoch:3d}  loss={loss.item():.4f}")

    # Top-5 for user 0 (taste = 0)
    with torch.no_grad():
        u_emb, i_emb = model.propagate(A_hat)
        scores = u_emb[0] @ i_emb.T
        for p in user_pos[0]:
            scores[p] = -float("inf")
        top = torch.topk(scores, k=5).indices.tolist()
    print(f"\nuser 0 (taste=item_id%%5==0) top-5: {top}")
    print(f"  of which item_id %% 5 == 0: {sum(1 for i in top if i % 5 == 0)}/5")


if __name__ == "__main__":
    main()
