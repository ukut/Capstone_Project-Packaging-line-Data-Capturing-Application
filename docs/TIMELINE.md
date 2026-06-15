# Capstone Timeline — Bottling Line App

**Submission deadline:** Sunday, July 12, 2026
**Time available from today (May 26, 2026):** 47 days
**Strategy:** 1 foundation week + 3 sprints (10–14 days each) + 1 submission week

---

## Week 0 — Foundation (May 26 – May 31)

**Goal:** Everything non-feature out of the way so Sprint 1 is pure development.

- [ ] Create GitHub repo, push the scaffold
- [ ] Add `quantic-grader` as collaborator
- [ ] Enable branch protection on `main` (CI must pass)
- [ ] Sign up for Render free tier, connect to repo
- [ ] Deploy current scaffold; verify `https://<your-app>.onrender.com/health` returns OK
- [ ] Create Trello board, add all stories from `docs/USER_STORIES.md`
- [ ] Add deployed URL and Trello link to README
- [ ] Upload representative-week bottling Excel
- [ ] Derive schema from Excel → add SQLAlchemy models in `app/models/`
- [ ] Wire models into `scripts/init_db.py`
- [ ] First sprint planning: pick stories from EPIC B for Sprint 1

**End-of-week deliverable:** Repo live, CI green, demo URL working with hello-world.

---

## Sprint 1 — Foundation & Operator MVP (June 1 – June 14)

**Goal:** A user can log in and enter the most important screen (production).

**Stories:** A-04, B-01, B-02, B-03, B-04, B-05, B-06, C-01, C-02

- [ ] Mon Jun 1: Sprint planning, move stories to Sprint 1 column
- [ ] Days 1–4: User model, auth service, login/logout routes, session middleware, role guards
- [ ] Days 5–6: Admin user management screens
- [ ] Days 7–8: Lookup table CRUD for SKUs, machines, downtime reasons, reject categories
- [ ] Days 9–11: Shift model, open shift, production entry screen with validation
- [ ] Days 12–13: Unit tests for auth service, integration tests for login flow, production entry tests
- [ ] Day 14 (Sun Jun 14): Sprint review — record short demo of operator logging in and entering production

**End-of-sprint deliverable:** Logged-in operator can start a shift, enter production, see it persist. Recorded sprint-review video. Deployed to Render with `?demo=true` showing real flow.

---

## Sprint 2 — Complete Operator + Supervisor Review (June 15 – June 28)

**Goal:** Full operator workflow + supervisor can review and approve.

**Stories:** C-03, C-04, C-05, C-06, C-07, D-01, D-02, D-03, D-05

- [ ] Mon Jun 15: Sprint planning
- [ ] Days 1–3: Downtime entry, quality check entry, material usage entry
- [ ] Days 4–5: Close-shift action; state transitions
- [ ] Days 6–8: Supervisor dashboard, shift review screen
- [ ] Days 9–10: Edit-with-reason workflow, audit log writes
- [ ] Days 11–12: Approve & lock action
- [ ] Days 13–14: Integration tests across the full lifecycle, sprint review recording

**End-of-sprint deliverable:** Full operator → supervisor workflow demonstrable end-to-end. Coverage > 70%.

---

## Sprint 3 — Polish, Analytics, Deploy (June 29 – July 8)

**Goal:** Anomaly detection, dashboards, Excel export, final deployment readiness.

**Stories:** D-04, E-01, E-02, E-03, E-04, F-01, F-02

- [ ] Mon Jun 29: Sprint planning
- [ ] Days 1–2: Anomaly rules — LongDowntime + HighRejectRate wired into supervisor screens (Strategy pattern already scaffolded ✅)
- [ ] Days 3–4: KPI dashboard with charts (server-rendered with Chart.js)
- [ ] Days 5–6: Excel export in legacy format
- [ ] Day 7: Audit trail viewer
- [ ] Day 8: Tune seed_synthetic for the demo (engineer at least 3 shifts with deliberate anomalies)
- [ ] Days 9–10: Final integration testing, fix any deployment issues on Render

**End-of-sprint deliverable:** Feature-complete app on Render demo URL. All tests passing. Coverage > 75%.

---

## Submission Week (July 9 – July 12)

**Goal:** Documentation finalized, demo recorded, submitted.

- [ ] Thu Jul 9: Finalize `docs/DESIGN.md` — fill in §4 (schema), §5.4 (coverage numbers), §9 (demo link)
- [ ] Fri Jul 10: Update README with all final links; close out remaining Trello cards
- [ ] Sat Jul 11: Record 15–20 min demo (Zoom, screen share, government ID shown). Re-record if it goes long. Upload to YouTube as unlisted.
- [ ] Sun Jul 12: Final review of submission, submit on Quantic dashboard

**End-of-week deliverable:** Submitted.

---

## Risk buffer

If you slip > 2 days in any sprint, immediately cut from this list (in this order):

1. E-03 — Bulk export
2. E-04 — Audit trail viewer (move to "stretch")
3. C-05 — Material usage detail (keep a minimal version, drop validation depth)
4. Power BI / external dashboard work
5. Mobile responsiveness

Never cut from: B (auth), C-01/02/06 (basic operator flow), D-01/02/05 (basic supervisor flow), F-04 (the demo recording itself).

---

## Daily rhythm

- Every weekday: open Trello, move cards, commit at end of day
- Every Sunday: 30-min self-retro — what slipped, what to compress next week
- After each sprint: short demo recording — these are your Capstone sprint-review artifacts
