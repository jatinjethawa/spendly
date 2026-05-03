# Spec: Registration

## Overview
This step adds `POST /register` so a new visitor can create an account. The GET route already renders the form; this step wires up the submission handler, server-side validation, password hashing, and the DB helper that inserts the new user row. On success the user is redirected to the login page; on failure the form is re-rendered with an error message and the name/email fields pre-filled.

## Depends on
- Step 1 — Database setup (`users` table, `get_db`, `init_db` already in place)

## Routes
- `POST /register` — accepts form submission, validates input, creates user, redirects to `/login` — public

## Database changes
No database changes. The `users` table (id, name, email, password_hash, created_at) is already created by `init_db()`. Two new helper functions are needed in `database/db.py`:
- `email_exists(email)` — returns `True` if the email is already registered
- `create_user(name, email, password_hash)` — inserts a new row, returns the new `id`

## Templates
- **Modify:** `templates/register.html`
  - Add `value="{{ name or '' }}"` to the name input so it re-fills on error
  - Add `value="{{ email or '' }}"` to the email input so it re-fills on error
  - Change `action="/register"` to `action="{{ url_for('register') }}"` (never hardcode URLs)

## Files to change
- `app.py` — convert `GET /register` to accept `GET` and `POST`; add POST handler logic
- `database/db.py` — add `email_exists` and `create_user`
- `templates/register.html` — pre-fill fields on error; fix hardcoded action URL

## Files to create
- `tests/test_registration.py` — endpoint and helper tests

## New dependencies
No new dependencies. `werkzeug` (already in `requirements.txt`) provides `generate_password_hash`.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — never f-strings or string concatenation in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` — never store plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic stays in `database/db.py` — no inline queries in route functions
- Use `abort()` for HTTP errors, not bare string returns
- Validate top-to-bottom; return on the **first** error encountered

### Validation order and messages
| Field | Rule | Error message |
|---|---|---|
| `name` | Non-empty after `.strip()` | "Name is required." |
| `email` | Non-empty after `.strip()` | "Email is required." |
| `password` | `len >= 8` | "Password must be at least 8 characters." |
| `email` | Not already in `users` | "An account with that email already exists." |

On any failure: re-render `register.html` with `error=<message>`, `name=<name>`, `email=<email>`. Never pre-fill the password field.

## Definition of done
- [ ] `GET /register` still returns 200 and renders the form
- [ ] Valid POST (unique email, password ≥ 8 chars) redirects to `/login` (302)
- [ ] After a valid POST, the new user row exists in the DB with a hashed (not plaintext) password
- [ ] Submitting with an empty name shows "Name is required." on the page
- [ ] Submitting with an empty email shows "Email is required." on the page
- [ ] Submitting with a 7-character password shows "Password must be at least 8 characters." on the page
- [ ] Submitting with an already-registered email shows "An account with that email already exists." on the page
- [ ] On any error, the name and email fields are pre-filled; the password field is empty
- [ ] All tests in `tests/test_registration.py` pass
- [ ] Full test suite passes with no regressions (`pytest`)
