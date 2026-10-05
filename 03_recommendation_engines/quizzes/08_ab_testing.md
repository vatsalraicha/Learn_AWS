# Quiz — A/B Testing & Experimentation (Module 34)

## A/B fundamentals

1. List the four prerequisites of a classical randomized A/B test. Give one production scenario where each one breaks.
2. Sample size for a 1% relative MDE on 5% baseline CTR is ~600k users total. Walk through the formula `N ≈ 16σ²/MDE²` to derive that number.
3. A 50/50 randomisation ends up 48/52. Why is this never noise? What's the chi-squared diagnostic, and what bugs typically cause it?
4. You ran 20 metrics on the same A/B; 1 reports `p < 0.05`. Why is this almost certainly a false positive, and which two corrections handle it?

## Method-specific

5. Explain team-draft interleaving in three sentences. Why does it give ~100× sample efficiency vs bucket A/B for ranking comparisons? What does it **not** measure?
6. Uber and DoorDash use switchback experiments. Explain why user-level A/B fails for dispatch policies, and what time-window length trade-off you're making.
7. CUPED reduces variance 30-50%. Why? Write the adjustment formula `Y_adj = Y − θ(X − E[X])` and explain the choice of θ.
8. Always-valid p-values (mSPRT) let you peek any number of times without inflating false positives. What's the trade-off vs a fixed-sample test?
9. Permanent holdouts cost you product quality on a small slice of users. Why is this cost considered worth paying for long-horizon measurement?
10. The surrogate index method (Athey, Chetty, Imbens 2019) estimates long-term effects from short-term proxies. Sketch the regression and what training data you need.

## Business-type differences

11. Why does Netflix lean heavily on **interleaving** while Uber leans heavily on **switchback** for the same underlying problem of "ranking quality"?
12. A B2B SaaS startup has 500 enterprise accounts and a 90-day sales cycle. They want to test a new lead-scoring model. Explain why bucket A/B is the wrong method, and propose three alternatives.
13. Meta's News Feed integrity tests use **cluster A/B** (randomising connected components of the social graph). Why not standard user-level A/B?
14. Ads platforms (Google, Meta) test new bidder models by combining A/B + lift studies + geo experiments + MMM calibration. Why is no single method enough?
15. A cold-email startup wants to A/B subject lines but reply rates are 2%. What's their actual unit of randomisation, and why is sender-domain rotation a separate experiment?

## Things that go wrong

16. A new model wins A/B with +5% engagement in week 1 but only +1% by week 4. Name two effects that explain this and which is which.
17. Your ad bidder A/B looks great offline but flat in production. The test is at 5% traffic; auctions are shared. What kind of interference are you likely hitting?
18. A holdout group's churn rate is higher than treatment's *and* you have a feature-store latency spike that occurred only for holdout users. What investigation do you do before drawing any conclusion?
19. A switchback test at DoorDash uses 30-minute windows with no washout. Why might the measured effect under-state the true effect?
20. Twyman's law says "anything surprisingly interesting is usually wrong." Give two concrete data-quality checks before you celebrate a +10% A/B result.

## Platform / org

21. What three signals does an experienced experimenter look for when a junior engineer presents A/B results? (Hint: one starts with "SRM.")
22. Netflix XP, Airbnb ERF, Booking ETF, Microsoft ExP — name two features each provides that a vanilla Statsig deployment doesn't, and one situation where Statsig is still the right choice.
23. CUPED, sequential testing, and switchback support — rank these three in the order you'd add them as your experimentation platform matures, with one-line rationale per step.
24. Your CEO asks "can we just look at the dashboard to see if this feature is working?" Explain in 3 sentences why this question is wrong, and what to do instead.
