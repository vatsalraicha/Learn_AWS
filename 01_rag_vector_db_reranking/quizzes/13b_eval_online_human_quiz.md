# Quiz — Module 13B (Online & Human Eval)

## Recall

1. What's the difference between shadow traffic and A/B testing? When do you use each?
2. State the rough sample-size formula for binary-metric A/B and one example.
3. What's interleaving, and why is it more sample-efficient?
4. Why does Likert "5 levels" outperform "10 levels"?
5. What do ASR and FRR stand for?

## Apply

6. You want to run an A/B detecting a 3pp lift on a 30% baseline thumbs-up rate. Roughly how many users per arm?
7. Outline the layered eval program a healthcare RAG product should run, with cadences for each layer.
8. Your team uses Ragas with the same model as both judge and generator. Identify the bias and propose a fix.

## Diagnose

9. After 3 days of A/B, your candidate is winning by 5pp on thumbs-up. PM wants to ship. What's the responsible response?
10. Your bot's offline faithfulness is 0.92, but red-team probes show it confabulates 30% of the time on out-of-corpus questions. What's missing from the offline eval?

## Defend

11. Argue against "we use thumbs-up rate as our only production metric."
12. Defend why "shadow traffic for ≥ 1 week" is non-negotiable before A/B for a high-stakes product, even when offline evals look perfect.

---

## Answer key

<details>
<summary>Click to reveal</summary>

1. **Shadow:** mirror live traffic to the candidate, log only, no user impact. Use first to catch regressions safely. **A/B:** send X% of real traffic to the candidate, users see it. Use when shadow is clean and you need real user-feedback signal.
2. `N per arm ≈ 16 · p · (1-p) / Δ²` for binary metric. Example: 30% baseline (p=0.3), detect 3pp lift (Δ=0.03) → ≈ 3,700 per arm.
3. Show users a *merged* result list from both pipelines for the *same* query; attribute click signals to A or B. Every query yields signal from both arms — ~10× sample-efficiency boost vs user-bucket A/B.
4. Central tendency bias — humans (and LLM judges) cluster on middle ratings on wide scales (3, 4, 5 of 7), avoiding 1, 2, 6, 7. Narrow scales with anchored levels force more deliberate choices and preserve signal.
5. **ASR** = Attack Success Rate (how often adversarial probes get a problematic answer). **FRR** = False Refusal Rate (how often the model refuses benign queries). Both matter — optimizing one alone can degrade the other.
6. ~3,700 per arm. At 1000 queries/day with 50/50 split → ~7-8 days minimum.
7. **Smoke evals** every PR (~30 examples, $0.50, blocks merge); **mid evals** on merge to main (~200 examples, $5); **full offline + red-team** nightly ($30-60); **shadow** for new pipelines (1-2 weeks); **A/B** with sequential testing on candidate (2+ weeks); **human SxS** quarterly for calibration; **production telemetry** continuous.
8. Self-preference bias. Mitigation: cross-family judge — pick a judge from a different model family than the generator (e.g., Claude generates → GPT-4 judges, or vice versa). Reduces the systematic favoring of one's own outputs.
9. Three days is too short. Risks: novelty effect (users notice "something different" and engage more, fades); insufficient sample size; weekly diurnal patterns not captured. Continue at least 2 weeks; check that the lift persists past week 1; check non-overlap of CIs; check downstream metrics aren't regressing.
10. Out-of-corpus questions aren't in the eval set. The offline set was built from "real" queries that have answers in the corpus; the system has no measured behavior on questions where it *should* refuse. Add adversarial probes to the eval set (out-of-knowledge questions, conflicting context, distraction); track ASR and FRR explicitly.
11. (a) Survivorship bias — only motivated users vote; happy quiet users invisible. (b) Doesn't localize failures (retrieval vs generation). (c) Lags by minutes-to-hours; a regression ships before signal arrives. (d) Misses silent quality drift on rare query types. Need it as ONE signal of many — not the gate.
12. Offline eval is over a fixed eval set; production has long-tail queries the eval set doesn't represent. Shadow catches: real query distribution, real corpus state, real failure modes (rate limits, prompt injections, weird Unicode, malformed inputs) that offline eval can't represent. For high stakes, untested behaviors on real queries are unacceptable risks.

</details>
