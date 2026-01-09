---
description: "Enforces Conventional Commits message formatting for all contributions."
alwaysApply: false
---

# Commit Message Rules

## Conventional Commits Standard

All commit messages must follow the **Conventional Commits** format:

```
<type>(optional scope): <description>
```

### Valid Types
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation changes
- `refactor` — code structural changes without new behavior
- `test` — test-related changes
- `chore` — tooling, configs, CI, formatting, dependencies
- `perf` — performance improvements
- `style` — formatting or styling changes without logic changes

### Examples (Good)

```
feat(api): add cron workload support
fix(worker): retry job scheduling on failure
docs: improve quickstart for developers
refactor: extract k8s templates into module
perf: improve reconcile loop efficiency
```

### Examples (Bad)

```
update stuff
fix bug
wip
temp
changes
misc
```

## Requirements

- Description must be written in lowercase (except proper names)
- Must not end with a period
- Should be concise and descriptive
- Should reference an issue when applicable (e.g., `Closes #123`)
- Should avoid vague wording

## Rationale

This rule enforces clear and consistent commit messages, improves history readability, and enables automated release tooling in the future.
