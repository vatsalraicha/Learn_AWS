# 48 — Agile + Scrum + Jira (Modern Reality)

## 1. Agile vs Scrum vs SAFe — the 2026 landscape

- **Agile Manifesto** (2001) — values + principles, not a process
- **Scrum** — most-adopted framework; sprints, backlog, ceremonies, roles
- **Kanban** — continuous flow; no sprints; WIP limits
- **Scrumban** — Scrum + Kanban hybrid
- **SAFe** (Scaled Agile Framework) — enterprise-scale; widely hated by practitioners; widely loved by middle managers
- **LeSS** / **Disciplined Agile** / **Spotify Model** — alternatives at scale

## 2. The Scrum cadence (in practice)

- **Sprint** — 1-4 weeks (2 most common)
- **Product Backlog** — prioritized list of work
- **Sprint Backlog** — work committed for the current sprint
- **Daily Standup** — 15min; what I did, what I'll do, blockers
- **Sprint Review** — demo at end
- **Sprint Retro** — what worked, what didn't, what to change
- **Sprint Planning** — pick from backlog for next sprint

Roles:
- **Product Owner** — prioritizes backlog, owns the "what"
- **Scrum Master** — facilitates ceremonies, removes blockers (often disappearing in 2026)
- **Dev Team** — builds it

## 3. The senior-engineer reality check

In 2026, mature orgs are dropping Scrum ceremonies. The trends:
- **Async standups** in Slack — no daily meeting
- **Continuous flow** (Kanban) instead of sprints
- **Story points abandoned** — measure cycle time + throughput instead
- **Retros every 2 weeks**, not every sprint
- **Demo days** monthly, not at end of every sprint

The Scrum-Master role is increasingly an EM responsibility, not a separate hire.

## 4. Jira essentials

Atlassian Jira Cloud is the dominant tool. Key concepts:
- **Project** — container of issues
- **Issue** — task (story, bug, epic, sub-task)
- **Board** — visualization (Scrum or Kanban)
- **Backlog** — prioritized list (Scrum)
- **Epic** → Stories → Sub-tasks hierarchy
- **Workflow** — issue state machine (To Do → In Progress → Done)
- **Sprint** — timeboxed iteration
- **Velocity** — story points completed per sprint (problematic metric)

## 5. The 2026 alternatives

| Tool | Why pick |
|---|---|
| **Linear** | Best DX, modern, opinionated, no setup |
| **Shortcut** (formerly Clubhouse) | Lightweight Jira |
| **Asana** | Cross-functional teams; non-tech projects too |
| **Monday.com** | Visual; project management beyond engineering |
| **Notion** | All-in-one workspace; lightweight project tracking |
| **GitHub Projects** | Tight GitHub integration |
| **Jira Product Discovery** | Atlassian's PM tool (separate from Jira Software) |

Engineering-tool-focused teams in 2026 increasingly leave Jira for Linear. Enterprise stays on Jira (Atlassian's lock-in via JSM, Confluence, ecosystem).

## 6. Backlog grooming + estimation

- **Story points** — relative sizing (Fibonacci: 1, 2, 3, 5, 8, 13). Increasingly debated.
- **T-shirt sizing** — XS/S/M/L/XL. Cheaper to apply.
- **Cycle time** — hours/days from "In Progress" to "Done". The metric that actually predicts.
- **Throughput** — items/sprint completed. Better than velocity.

The DORA-derived insight: cycle time is more honest than velocity. Velocity is gamed; cycle time is harder to fake.

## 7. Agile for AI/ML teams (the special case)

Standard Scrum struggles with AI/ML work because:
- Research has unpredictable timelines
- Experiments can fail (the result is "we learned X, no shippable artifact")
- Deliverables are model versions, not user stories
- "Done" is fuzzy (95% accuracy = ship? 98% = ship?)

Patterns that work:
- **Two-track agile** — discovery track (research) + delivery track (shippable improvements)
- **OKRs** for research goals; Kanban for ML platform/eng work
- **Demo every other week** of either: working model OR negative result
- **Time-box research** explicitly (e.g., "2 weeks to evaluate, then decide")

## 8. The Scrum anti-patterns

1. **Velocity as KPI** — gameable; encourages estimate inflation
2. **No retro action items** — retros become rituals with no improvement
3. **Story-point-poker as decision-making** — disagreement on point estimates means specification gap, not estimate gap
4. **Daily standup as status report** — should be coordination, not reporting
5. **No definition of done** — "done" varies per PR, leading to half-shipped work
6. **Sprint goal = "complete all stories"** — should be an outcome, not a list

## 9. Quick self-check

1. What's the difference between Scrum and Kanban?
2. Why is cycle time a better metric than velocity?
3. What's two-track agile and when use it?
4. Why are senior orgs dropping story points?
5. Name one Scrum anti-pattern.

(Answers: Scrum = timeboxed sprints with ceremonies, Kanban = continuous flow with WIP limits; cycle time is harder to game and directly measures throughput, velocity inflates with practice; one track for discovery/research, another for shippable delivery — fits AI/ML work; gameable, time-consuming, doesn't predict better than t-shirt sizes or just splitting work; velocity-as-KPI, story-poker as decision-making, no retro action items, daily-standup-as-status-report, no DoD, sprint-goal-as-list.)
