"""Module 12 — Tiny generative recommender.

Decoder-only transformer trained to predict next item ID. The kernel of TIGER /
HSTU at a toy scale (no semantic IDs; treating item IDs as the vocab).

Run:  python 12_generative_rec.py
"""
from __future__ import annotations
import torch
import torch.nn as nn


class GenRec(nn.Module):
    def __init__(self, vocab_size, d_model=64, n_heads=2, n_layers=2, max_len=50):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(max_len, d_model)
        layer = nn.TransformerEncoderLayer(d_model, n_heads, dim_feedforward=4 * d_model, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, n_layers)
        self.head = nn.Linear(d_model, vocab_size)
        self.max_len = max_len

    def forward(self, seq):
        B, L = seq.shape
        pos = torch.arange(L, device=seq.device).unsqueeze(0).expand(B, L)
        x = self.tok_emb(seq) + self.pos_emb(pos)
        mask = nn.Transformer.generate_square_subsequent_mask(L).to(seq.device)
        h = self.encoder(x, mask=mask)
        return self.head(h)

    @torch.no_grad()
    def generate(self, prefix, n=10, top_k=5):
        cur = prefix.clone()
        for _ in range(n):
            inp = cur[:, -self.max_len:]
            logits = self.forward(inp)[:, -1, :]
            if top_k is not None:
                vals, idx = logits.topk(top_k, dim=-1)
                probs = torch.softmax(vals, dim=-1)
                sample_idx = torch.multinomial(probs, 1)
                next_item = idx.gather(1, sample_idx)
            else:
                next_item = logits.argmax(-1, keepdim=True)
            cur = torch.cat([cur, next_item], dim=-1)
        return cur


def make_sequences(n_users=50, n_items=100, max_seq_len=20, seed=0):
    rng = torch.Generator().manual_seed(seed)
    sequences = []
    for u in range(n_users):
        taste = u % 5
        length = torch.randint(8, max_seq_len, (1,), generator=rng).item()
        items = []
        for _ in range(length):
            if torch.rand(1, generator=rng).item() < 0.75:
                items.append(taste + 1 + torch.randint(0, n_items // 5 - 1, (1,), generator=rng).item() * 5)
            else:
                items.append(torch.randint(1, n_items, (1,), generator=rng).item())
        sequences.append(items)
    return sequences


def main():
    torch.manual_seed(0)
    n_items, max_len = 100, 20
    model = GenRec(vocab_size=n_items + 1, d_model=32, max_len=max_len)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)

    sequences = make_sequences(n_users=100, n_items=n_items, max_seq_len=max_len)
    inputs, targets = [], []
    for seq in sequences:
        if len(seq) < 2:
            continue
        s = seq[:max_len]
        in_seq = s[:-1] + [0] * (max_len - len(s) + 1)
        tg_seq = s[1:] + [0] * (max_len - len(s) + 1)
        inputs.append(in_seq[:max_len])
        targets.append(tg_seq[:max_len])
    inputs = torch.tensor(inputs)
    targets = torch.tensor(targets)

    for epoch in range(30):
        logits = model(inputs)
        loss = nn.functional.cross_entropy(
            logits.reshape(-1, logits.size(-1)),
            targets.reshape(-1),
            ignore_index=0,
        )
        opt.zero_grad(); loss.backward(); opt.step()
        if epoch % 10 == 0:
            print(f"epoch {epoch:3d}  loss={loss.item():.4f}")

    # Generate continuation for user 0 (taste=1)
    test_prefix = torch.tensor([sequences[0][:5]])
    print(f"\nuser 0 history: {sequences[0][:5]}")
    gen = model.generate(test_prefix, n=5, top_k=5)
    new_items = gen[0, 5:].tolist()
    print(f"generated next 5: {new_items}")
    print(f"of which match taste (id %% 5 == 1): {sum(1 for i in new_items if i % 5 == 1)}/5")


if __name__ == "__main__":
    main()
