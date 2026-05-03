# Spec: Login and Logout

## Overview
This step wires up the login form submission and the logout action so users can authenticate
and end their session. `POST /login` validates credentials against the `users` table, stores
the user ID in a Flask session on success, and re-renders the form on failure. `GET /logout`
clears the session and redirects to the landing page. After this step, the app has end-to-end
auth: register → login → (future protected pages) → logout.

## Depends on
- Step 1 — Database setup (`users` table, `get_db` in place)
- Step 2 — Registration (`create_user`, `email_exists` in place; login page renders)

## Routes
- `POST /login` — accepts form submission, validates credentials, sets session, redirects to `/` on success — public
- `GET /logout` — clears session, redirects to `/` — logged-in (no hard guard yet; safe to call when logged out)

## Database changes
No new tables or columns. One new helper function is needed in `database/db.py`:
- `get_user_by_email(email)` — returns the full user row (as `sqlite3.Row`) or `None` if not found

## Templates
- **Modify:** `templates/login.html`
  - Add `method="POST"` and `action="{{ url_for('login') }}"` to the `<form>` tag
  - Display `{{ error }}` when present (same pattern as `register.html`)
  - Pre-fill the email input with `value="{{ email or '' }}"` on error
  - Never pre-fill the password field
- **Modify:** `templates/base.html`
  - Show a "Logout" nav link when `session.user_id` is set
  - Hide "Login" and "Register" nav links when the user is already logged in

## Files to change
- `app.py`
  - Add `session` and `abort` to Flask imports (if not already imported)
  - Set `app.secret_key` from `os.environ.get('SECRET_KEY', 'dev-secret-key')` immediately after `app = Flask(__name__)`
  - Convert `GET /login` to accept `GET` and `POST`; add POST handler logic
  - Implement `GET /logout`: call `session.clear()`, redirect to `url_for('landing')`
- `database/db.py` — add `get_user_by_email(email)`
- `templates/login.html` — add form action, error display, email pre-fill
- `templates/base.html` — conditional nav links based on `session`

## Files to create
- `tests/test_login_logout.py` — endpoint and session tests

## New dependencies
No new dependencies. `werkzeug` (already in `requirements.txt`) provides `check_password_hash`.
Flask sessions use `itsdangerous` which ships with Flask.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — never f-strings or string concatenation in SQL
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic stays in `database/db.py` — no inline queries in route functions
- Use `abort()` for HTTP errors, not bare string returns
- Store only `user_id` (integer) in the session — never store password hash or full user object
- `app.secret_key` must be set before any session use; read from env so it can be overridden in production

### Validation order and messages (POST /login)
| Check | Rule | Error message |
|---|---|---|
| `email` | Non-empty after `.strip()` | "Email is required." |
| `password` | Non-empty | "Password is required." |
| user lookup | `get_user_by_email(email)` returns a row | "Invalid email or password." |
| password | `check_password_hash(row['password_hash'], password)` is `True` | "Invalid email or password." |

On any failure: re-render `login.html` with `error=<message>` and `email=<email>`. Never pre-fill password.
Use a single generic message ("Invalid email or password.") for both the missing-user and wrong-password
cases to avoid leaking whether an email is registered.

## Definition of done
- [ ] `GET /login` returns 200 and renders the login form
- [ ] Valid POST with correct credentials redirects to `/` (302) and sets a session cookie
- [ ] After a valid POST, `session['user_id']` equals the logged-in user's DB id
- [ ] Submitting with an empty email shows "Email is required." on the page
- [ ] Submitting with an empty password shows "Password is required." on the page
- [ ] Submitting with a non-existent email shows "Invalid email or password." on the page
- [ ] Submitting with correct email but wrong password shows "Invalid email or password." on the page
- [ ] On any error, the email field is pre-filled; the password field is empty
- [ ] `GET /logout` clears the session and redirects to `/` (302)
- [ ] After logout, `session.get('user_id')` is `None`
- [ ] `base.html` shows "Logout" link when logged in and hides "Login"/"Register"
- [ ] All tests in `tests/test_login_logout.py` pass
- [ ] Full test suite passes with no regressions (`pytest`)
