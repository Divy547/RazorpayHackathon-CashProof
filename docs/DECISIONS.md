# Locked Architecture Decisions

1. Deterministic financial truth.
2. Evidence-first decisions.
3. One bounded investigator; no multi-agent mesh.
4. No Celery/Redis initially.
5. Modular monolith.
6. INR-only MVP with explicit currency.
7. S4/S5 text/alias-derived links route to HUMAN_REVIEW.
8. AUTO_RESOLVED requires exact target-set equality.
9. GroundTruth is evaluator-only and technically isolated from production/AI ports.
10. AI confidence is never a gate input.
11. `case_id` identifies one case instance and is not reused across runs; `settlement_id` is the cross-run comparison key.
12. No exact LLM reproducibility claim.
13. Use `ResolutionProposal`.
14. Adjustment sign: positive increases net, negative decreases net.
15. Candidate windows: +/-7 days reference-backed; +/-3 days S4/S5.
16. Tax is stored as `tax_on_fee_minor`; generator computes 18% once with half-up rounding.
17. Partial grouped matches: exact set may auto-resolve; strict subset fails evidence completeness; default UNRESOLVED; full-set proposal with uniquely plausible unmatched members routes HUMAN_REVIEW.
18. LedgerEntry amount is an unsigned magnitude interpreted by direction.
19. Settlement deposited net equals the sum of settlement-item computed nets.
20. Netted refund total equals the included refunds for that payment.
21. A LedgerEntry may be the final target of at most one Resolution.
22. `rule_version` identifies the deterministic engine code revision used by a benchmark run.
23. Investigator budgets are enforced from the first AI implementation.
24. GroundTruth is available only through benchmark evaluator interfaces.
25. Evidence and failing gate checks must be visible to reviewers in the Exception Center.
