# Quiz — Tech Stack & Reference Architectures (Modules 32-33)

## Module 32 — The recsys tech stack

1. Why are feature-store online/offline parity and point-in-time correctness considered non-negotiable?
2. The "right" ANN library depends on scale. For 100M vectors with strict 10ms p99, which would you pick and why?
3. CUPED reduces required A/B sample size by 30-50%. Why is this load-bearing for teams running concurrent experiments?
4. Embedding-cache choice (Redis vs ScyllaDB vs DynamoDB) depends on what trade-off?
5. A vendor like Amazon Personalize abstracts the whole stack. When does it make sense to use it instead of building?

## Module 33 — Reference architectures

1. A 100-person B2B SaaS company wants to build a "Netflix-style recommender." What stack do you propose for their first iteration?
2. The classic build-vs-buy mistake is building before scale demands it. Give two signals that say "you should still use the vendor."
3. Mid-stage companies often try to centralise everything in one feature store. What's the trade-off and when does it become net-positive?
4. The hyperscaler ML org chart has a 50-person platform team. What does that team produce that no individual surface team would?
5. Your CEO says "we want to build our own DLRM in 6 months." You're at $30M ARR. How do you push back constructively?
