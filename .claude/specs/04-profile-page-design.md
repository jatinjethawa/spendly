# Spec: Profile Page Design

## Overview
This step implements the `/profile` page, giving logged-in users a view of their account
details (name, email, member-since date). It introduces the first login-guarded route in
Spendly: unauthenticated visitors are redirected to `/login`. A new DB helper
`get_user_by_id` retrieves the user row by session ID. The page is intentionally read-only
at this stage — editing profile details is out of scope until a later step.

## Depends on
- Step 1 — Database setup (`users` table and `get_db()` in place)
- Step 2 — Registration (users can be created)
- Step 3 — Login and Logout (`session["user_id"]` is set on login; logout clears it)

## Routes
- `GET /profile` — renders the profile page with the logged-in user's details — logged-in only (redirect to `/login` if not authenticated)

## Database changes
No new tables or columns. One new helper function is needed in `database/db.py`:
- `get_user_by_id(user_id)` — returns the full user row (`id`, `name`, `email`, `created_at`) or `None` if not found

## Templates
- **Create:** `templates/profile.html`
  - Extends `base.html`
  - Displays: full name, email address, member-since date (formatted as "DD Mon YYYY")
  - Uses CSS variables for all colours — no hardcoded hex values
  - No edit form at this stage — display only
- **Modify:** `templates/base.html`
  - Ensure the nav "Profile" link points to `url_for('profile')` and is only shown when logged in

## Files to change
- `app.py`
  - Replace the stub `GET /profile` with a real implementation:
    - If `session.get("user_id")` is falsy, `redirect(url_for("login"))`
    - Call `get_user_by_id(session["user_id"])` from `database/db.py`
    - If the returned user is `None`, call `abort(404)`
    - Render `profile.html`, passing `user=user`
  - Add `get_user_by_id` to the `database.db` import line
- `database/db.py` — add `get_user_by_id(user_id)`
- `templates/base.html` — add "Profile" nav link (visible only when logged in)
- `templates/profile.html` — create new template (see above)

## Files to create
- `templates/profile.html` — profile display page
- `tests/test_profile.py` — route and access-control tests

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — never f-strings or string concatenation in SQL
- Passwords hashed with werkzeug — do not expose `password_hash` to the template
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic stays in `database/db.py` — no inline queries in route functions
- Use `abort(404)` if `get_user_by_id` returns `None`
- Use `redirect(url_for("login"))` (not `abort`) for unauthenticated access
- Pass only safe fields to the template (`id`, `name`, `email`, `created_at`) — never pass `password_hash`

## Definition of done
- [ ] `GET /profile` returns 200 and renders the profile page for a logged-in user
- [ ] The profile page displays the user's name, email, and member-since date
- [ ] Member-since date is formatted as "DD Mon YYYY" (e.g. "01 Jan 2026")
- [ ] `GET /profile` redirects to `/login` (302) when no session exists
- [ ] After redirect to login, the user can log in and then access `/profile` successfully
- [ ] The nav bar shows a "Profile" link only when the user is logged in
- [ ] `password_hash` is never passed to or rendered in any template
- [ ] `get_user_by_id` returns `None` for an unknown ID and the route calls `abort(404)`
- [ ] All tests in `tests/test_profile.py` pass
- [ ] Full test suite passes with no regressions (`pytest`)
