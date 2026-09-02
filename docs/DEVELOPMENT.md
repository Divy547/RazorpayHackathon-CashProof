# Development Workflow

## Roles

ChatGPT = Architect / Tech Lead
Claude = Senior Engineer / adversarial reviewer
Agy = Implementation Engineer
Human developer = final product validator

## Normal loop

1. ChatGPT defines a bounded task.
2. Agy inspects relevant files and proposes a plan.
3. Claude reviews when domain, architecture, benchmark or AI risk is material.
4. ChatGPT approves/modifies the plan.
5. Agy implements.
6. Agy runs tests and validation.
7. Claude adversarially reviews when warranted.
8. ChatGPT performs final architecture review.
9. Human validates product behavior.

Tiny tasks may use Agy -> tests -> human review.

Never let parallel agents edit the same files. Parallelize only independent work and use separate branches/worktrees.

## Phase order

0. repository foundation + architecture enforcement
1. domain core
2. synthetic generator
3. deterministic finance/reconciliation engine
4. gate + resolution
5. first benchmark
6. S1-S6 scenarios
7. evidence
8. AI investigator
9. batch runner + CLI
10. API
11. frontend
12. hardening

## Definition of done

Implementation exists, relevant tests exist and pass, architecture boundaries remain valid, locked rules are respected, docs are updated when decisions change, and known critical failures are reported.
