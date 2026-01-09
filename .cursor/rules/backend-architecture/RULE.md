---
description: "Lightweight clean code and directory structure guidelines for backend code in this organization."
alwaysApply: true
---

# Backend Clean Code Rules (Lightweight)

These rules apply to **backend code** in this organization. They are meant to keep the code simple, readable, and easy to change, without enforcing a heavy or complex architecture.

## 1. Small, Focused Functions

- Functions should do **one thing well**.
- Prefer several small functions over a single large, monolithic one.
- As a rule of thumb, avoid functions longer than ~30–40 lines unless there is a clear, documented reason.

### Good

```python
def create_application(dto: ApplicationCreateDTO) -> Application:
    validate_application_dto(dto)
    app = build_application(dto)
    save_application(app)
    return app
```

### Bad

```python
def create_application(request):
    # 150+ lines of parsing, validation, DB calls, logging, retries, etc.
    ...
```

---

## 2. Meaningful Names

- Names must describe **what** something is or **what** it does.
- Avoid vague names such as `data`, `obj`, `doStuff`, `handle`, `manager`, `x`, `n`.
- Prefer full words over cryptic abbreviations, especially in public APIs.

### Good

```python
max_retries = 3
deployment_name = build_deployment_name(application)
```

### Bad

```python
x = 3
n = build(app)
```

---

## 3. Avoid Duplication

- If the same logic appears 3 times or more, extract it into a function or shared module.
- Shared behavior should live in a clearly named place (for example: `shared/`, `common/`, `core/`), not copied into multiple handlers or services.

### Good

```python
def normalize_name(raw: str) -> str:
    return raw.strip().lower()

name = normalize_name(dto.name)
```

### Bad

```python
name = dto.name.strip().lower()
another_name = another_dto.name.strip().lower()
```

---

## 4. One Main Responsibility per File

- Avoid massive files that mix handlers, services, models, repositories, helpers, and constants all together.
- Prefer splitting files by their main responsibility or role.

Examples of better separation:

- `application_handlers.py`
- `application_service.py`
- `application_repository.py`
- `application_models.py`

This keeps navigation and refactoring simpler for backend codebases.

---

## 5. Fail Fast and Be Explicit

- Validate inputs early and fail fast when something is invalid.
- Prefer clear, explicit errors over silent failures or hidden side effects.
- Do not swallow exceptions without at least logging and providing some context.

### Good

```python
if dto.replicas <= 0:
    raise ValueError("replicas must be a positive integer")
```

### Bad

```python
try:
    deploy(dto)
except Exception:
    pass  # silently ignore
```

---

## 6. Backend-Specific Considerations

- Business rules should not be buried inside infrastructure code (DB, Kubernetes, HTTP clients, etc.).
- Side-effect-heavy code (I/O, network, DB) should be easy to spot and ideally isolated in well-named functions or modules.
- When in doubt, optimize for clarity over cleverness.

---

## 7. Directory Structure for Backend Code

Backend projects should follow a simple and predictable directory structure.

### Recommended layout

```text
app/
  <feature>/
    api/
    core/
    infra/
  shared/
  tests/
```

#### Meaning of each folder

- `api/`  
  HTTP handlers, controllers, CLI entrypoints, DTOs, serializers.  
  No business logic.

- `core/`  
  Business logic, services, validation, processing.  
  Code in `core/` should be testable without DB, HTTP, or Kubernetes.

- `infra/`  
  Integrations with external systems (DB, queues, Kubernetes, HTTP clients, file storage, caches, cloud SDKs, etc.).  
  No business rules.

- `shared/`  
  Utilities or shared code used across multiple features, but with a clear purpose  
  (e.g., logging, tracing, configuration, metrics, error handling).

- `tests/`  
  Tests should roughly mirror the structure of `app/` for easier discovery and maintenance.

### Feature-based organization

Features should be grouped by domain rather than technical buckets:

```text
app/
  applications/
  clusters/
  jobs/
  users/
```

This is preferred over top-level technical buckets such as:

```text
controllers/
models/
services/
utils/
helpers/
misc/
```

These patterns lead to unclear ownership, hard navigation, and larger merge conflicts.

### Rule: Avoid Generic Dump Folders

The following generic folders **must not** be used as a dumping ground for unrelated code:

- `utils/`
- `helpers/`
- `misc/`
- `tmp/`
- `stuff/`

If something is important enough to exist, it should live:

- inside a feature folder (e.g., `applications/core/`), or
- inside a well-defined shared module (`shared/logging/`, `shared/config/`, etc.).

---

## Rationale

These backend clean code and directory structure rules are intentionally simple and pragmatic. They:

- improve readability and maintainability,
- reduce mental overhead for new contributors,
- make refactoring easier over time,
- and create a consistent baseline structure for all backend services in this organization.

More specific rules for architecture, layers, or domains can be added later as needed, but this clean code baseline and directory layout should remain valid for most backend projects.
