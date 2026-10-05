# Quiz 01 — Git foundations + GitHub collaboration (Parts A–B)

Covers modules 1–14.

---

## Section 1 — Git internals (modules 1–3)

1. **What are the four Git object types?**
   <details><summary>Answer</summary>blob, tree, commit, tag. Each identified by SHA-1 of its content (SHA-256 in opt-in repos / future Git 3.0). Stored under `.git/objects/`.</details>

2. **What does `git commit` actually do internally?**
   <details><summary>Answer</summary>Creates a new commit object whose `tree` SHA points to a snapshot of staged changes, with `parent` = previous HEAD. Then moves the current branch ref forward to point at the new commit.</details>

3. **After `git reset --hard HEAD~3`, what happens to the "deleted" commits?**
   <details><summary>Answer</summary>They remain in `.git/objects/` (immutable). The branch ref moved back. The reflog still references them for 90 days (configurable via `gc.reflogExpire`). `git gc --prune=now` after expiry actually deletes them.</details>

4. **Why does `git rebase` produce commits with different SHAs?**
   <details><summary>Answer</summary>A commit's SHA is a function of its content + its parent. Rebase changes the parent → new SHA. Even with identical diff and message, the SHA differs.</details>

5. **What's the difference between `core.fsmonitor=true` and `core.untrackedCache=true`?**
   <details><summary>Answer</summary>`fsmonitor` uses OS file-watching APIs (since 2.36) to skip scanning unchanged files in `git status`. `untrackedCache` caches the list of untracked files between runs. Both speed up `status` on huge repos.</details>

6. **What is `merge.conflictStyle = zdiff3` and why use it?**
   <details><summary>Answer</summary>Conflict marker format that includes the common ancestor block between the two competing versions, helping you understand *why* the conflict exists. Available since Git 2.35. Recommended for senior usage.</details>

---

## Section 2 — Branching, merging, rebasing (modules 4, 6)

7. **When should you rebase vs merge a feature branch?**
   <details><summary>Answer</summary>Rebase your own private (unshared) branches; merge anything that's been shared. Rebase rewrites history (creates new SHAs); if others have pulled the old branch, their local refs break.</details>

8. **Why use `git push --force-with-lease` instead of `git push --force`?**
   <details><summary>Answer</summary>`--force-with-lease` aborts if the remote moved since your last fetch (someone else pushed in between), preventing accidental overwrite of others' work. Plain `--force` overwrites unconditionally.</details>

9. **What does `git rebase -i HEAD~5` let you do?**
   <details><summary>Answer</summary>Interactive rebase of the last 5 commits: `pick`, `reword`, `edit`, `squash`, `fixup`, `drop`, `reorder`, `exec`. Used for cleaning up commit history before pushing/PR.</details>

10. **What's `git rerere`?**
    <details><summary>Answer</summary>Reuse Recorded Resolution. Remembers each conflict resolution and replays it automatically the next time the same conflict reappears. Enable: `git config --global rerere.enabled true`. Saves time on repeated rebases.</details>

11. **What's the difference between `git reset --soft`, `--mixed`, `--hard`?**
    <details><summary>Answer</summary>All three move the branch ref. `--soft` keeps index + working tree untouched. `--mixed` (default) resets index but keeps working tree. `--hard` resets both index and working tree (DESTRUCTIVE).</details>

12. **What's `.git-blame-ignore-revs` for?**
    <details><summary>Answer</summary>File listing commit SHAs that `git blame` should skip. Useful after big formatter PRs (e.g., black/ruff) so blame shows the real author of each line, not the formatter commit. Honored by GitHub UI too.</details>

---

## Section 3 — GitHub collaboration (modules 8–14)

13. **In a CODEOWNERS file, when multiple rules match a path, which wins?**
    <details><summary>Answer</summary>Last matching rule wins. Put broader rules earlier, specific rules later.</details>

14. **What's the difference between branch protection rules and Rulesets?**
    <details><summary>Answer</summary>Rulesets (GA 2023) are the modern, more powerful replacement. They stack additively (multiple rulesets compose), are visible to non-admins, support layered org→repo policies, and (as of Feb 2026) include the Required Reviewer rule with negation patterns. Old branch protection rules still work but Rulesets are the recommended path.</details>

15. **What's the difference between PAT classic and PAT fine-grained?**
    <details><summary>Answer</summary>Classic: coarse scopes (`repo`, `workflow`), all-or-nothing, no required expiry. Fine-grained: per-permission, per-repo scoping, required expiry (max 1 year), org-approval required for org-owned resources. Always prefer fine-grained for new tokens.</details>

16. **Why use SSH signing over GPG signing for commits?**
    <details><summary>Answer</summary>Reuses your existing SSH key (no new key to manage). Simpler setup. Supported since Git 2.34. Same security guarantees as GPG. Configure: `gpg.format = ssh`, `user.signingkey = ~/.ssh/id_ed25519.pub`.</details>

17. **What's `gh repo sync` for?**
    <details><summary>Answer</summary>Syncs your fork with the upstream repo (the source you forked from). One command replaces fetch + checkout + rebase + push. Useful when working in InnerSource fork workflows.</details>

18. **What are the three PR merge strategies and when to use each?**
    <details><summary>Answer</summary>**Merge commit** (preserves branch's individual commits + creates merge commit; rarely used in trunk-based). **Squash and merge** (combines all branch commits into ONE on main; most common for trunk-based). **Rebase and merge** (replays each commit individually on main; for clean-history branches).</details>

19. **What is the `merge_group` event in GitHub Actions for?**
    <details><summary>Answer</summary>It fires when a PR is added to a merge queue. The queue creates a tentative commit (applying this PR on top of main + any PRs ahead of it) and re-runs CI on that commit before merging. Prevents semantic conflicts where two PRs each pass CI alone but break when merged together.</details>

20. **What's an "outside collaborator" vs an org member?**
    <details><summary>Answer</summary>Outside collaborator = not an org member; granted access to specific repos only. Counts as a separate billing category. Use for contractors, vendors, auditors. Quarterly review the list.</details>
