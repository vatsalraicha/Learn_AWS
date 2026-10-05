"""Module 9 — Tiny SASRec self-attentive sequential recommender.

Run:  python 09_sasrec.py
"""
from __future__ import annotations
import torch
import torch.nn as nn


class SASRec(nn.Module):
    def __init__(self, n_items: int, d_model: int = 64, n_heads: int = 2, n_layers: int = 2, max_len: int = 50):
        super().__init__()
        self.item_emb = nn.Embedding(n_items + 1, d_model, padding_idx=0)
        self.pos_emb = nn.Embedding(max_len, d_model)
        layer = nn.TransformerEncoderLayer(d_model, n_heads, dim_feedforward=4 * d_model, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, n_layers)
        self.max_len = max_len

    def forward(self, seq):
        B, L = seq.shape
        pos = torch.arange(L, device=seq.device).unsqueeze(0).expand(B, L)
        x = self.item_emb(seq) + self.pos_emb(pos)
        mask = nn.Transformer.generate_square_subsequent_mask(L).to(seq.device)
        h = self.encoder(x, mask=mask)
        # score each position against all items
        logits = h @ self.item_emb.weight.T
        return logits


def generate_synthetic(n_users=50, n_items=200, max_seq_len=20, seed=0):
    """Each user has a 'taste' = preferred item-id mod 10; sequences sampled to favor those."""
    rng = torch.Generator().manual_seed(seed)
    sequences = []
    for u in range(n_users):
        taste = u % 10
        items = []
        for _ in range(torch.randint(5, max_seq_len, (1,), generator=rng).item()):
            if torch.rand(1, generator=rng).item() < 0.7:
                items.append(taste + 1 + (torch.randint(0, n_items // 10 - 1, (1,), generator=rng).item() * 10))
            else:
                items.append(torch.randint(1, n_items, (1,), generator=rng).item())
        sequences.append(items)
    return sequences


def make_batch(sequences, max_len=20, pad_id=0):
    """Build (input, target, mask) tensors for next-item prediction training."""
    inputs, targets = [], []
    for seq in sequences:
        if len(seq) < 2:
            continue
        in_seq = seq[:-1][:max_len - 1]
        tgt_seq = seq[1:][:max_len - 1]
        in_seq = in_seq + [pad_id] * (max_len - len(in_seq))
        tgt_seq = tgt_seq + [pad_id] * (max_len - len(tgt_seq))
        inputs.append(in_seq)
        targets.append(tgt_seq)
    return torch.tensor(inputs), torch.tensor(targets)


def main():
    torch.manual_seed(0)
    n_items, max_len, n_users = 200, 20, 100
    model = SASRec(n_items=n_items, d_model=32, n_heads=2, n_layers=2, max_len=max_len)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    sequences = generate_synthetic(n_users=n_users, n_items=n_items, max_seq_len=max_len, seed=0)
    inputs, targets = make_batch(sequences, max_len=max_len)
    print(f"Training data: {inputs.shape[0]} sequences of length {inputs.shape[1]}")

    for epoch in range(30):
        logits = model(inputs)                                  # (B, L, V)
        loss = nn.functional.cross_entropy(
            logits.reshape(-1, logits.size(-1)),
            targets.reshape(-1),
            ignore_index=0,
        )
        opt.zero_grad(); loss.backward(); opt.step()
        if epoch % 5 == 0:
            print(f"epoch {epoch:3d}  loss={loss.item():.4f}")

    # Inference: predict next item for user 0's history
    test_seq = sequences[0][:5]
    inp = torch.tensor([test_seq + [0] * (max_len - len(test_seq))])
    with torch.no_grad():
        logits = model(inp)[0, len(test_seq) - 1]
        top = logits.topk(5).indices.tolist()
    print(f"\nuser 0 history (taste=item_id%%10==1): {test_seq}")
    print(f"top-5 next item predictions: {top}")
    print(f"of which match taste (id %% 10 == 1): {sum(1 for i in top if i % 10 == 1)}/5")


if __name__ == "__main__":
    main()
