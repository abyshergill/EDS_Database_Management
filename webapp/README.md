# EDS Data Collection System — Web Edition (Django)

A Django rewrite of the desktop (Tkinter) EDS application. It stores EDS analysis
records (component name, VHX image + remark, EDS image + remark, general remark),
requires login for everything, and keeps a full change history.

## Roles

| Capability | Normal user | Administrator |
|---|:-:|:-:|
| Sign in / change own password | ✅ | ✅ |
| Create, view, search, edit, delete EDS records | ✅ | ✅ |
| See per-record change history | ✅ | ✅ |
| Create / edit / deactivate / delete user accounts, reset passwords | ❌ | ✅ |
| Global activity log (filter by user, action, component) | ❌ | ✅ |

There is **no self-registration**. Only an administrator (a user with `is_staff`)
can create accounts. Admins cannot demote, deactivate or delete themselves.

## History / audit trail

Every record change writes a `RecordHistory` row in the same database
transaction as the change:

- **create**: who created it and the initial values
- **update**: only the fields that changed, with old → new values (image changes
  are logged as uploaded / replaced / removed). Saving without changes logs nothing.
- **delete**: who deleted it and the last values

History stays readable after a record or a user is deleted, because the
component name, record id and username are stored on the entry. The audit
trail is read-only in Django admin. Logins, failed logins and account
management actions also go to `logs/eds_web.log`.

## Quick start

```bash
cd webapp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser      # first administrator
python manage.py runserver
```

Then open http://127.0.0.1:8000 and sign in.

### Import data from the desktop app

```bash
python manage.py import_legacy_db ../data/eds.db
```

This imports records and their images. Desktop user accounts are **not** imported,
because they used unsalted SHA-256 hashes; recreate them from the *User accounts* page.
`created_by` is matched to a web user with the same username if one exists.

## Tests

```bash
python manage.py test
```

The tests cover: login enforcement on every page, admin-only account management,
normal-user restrictions, record CRUD (including images, validation and file
cleanup), history logging for create/update/delete, image serving and the legacy import.

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev key | **Set in production** |
| `DJANGO_DEBUG` | `1` | Set to `0` in production (also enables secure cookies) |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names |
| `DJANGO_DB_PATH` | `webapp/db.sqlite3` | SQLite file location |

Sessions expire after 1 hour or when the browser closes. Uploaded images go to
`webapp/media/` and are served only through an authenticated view, never as
public files. Images are limited to 10 MB.

## Security

| Threat | Protection |
|---|---|
| Brute-force login | Lockout after 5 failed attempts per username (20 per IP) for 15 min, checked **before** the password is verified (`accounts/throttle.py`). Failed logins and lockouts are logged. |
| SQL injection | All queries go through the Django ORM (parameterised). No raw SQL on user input. |
| CSRF | `CsrfViewMiddleware` + token in every form. All state changes (create/update/delete/logout) are POST-only. |
| XSS | Template auto-escaping everywhere; JS uses `textContent`. |
| Clickjacking / sniffing | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin` |
| Session theft | HttpOnly + SameSite cookies, Secure cookies, SSL redirect and HSTS when `DJANGO_DEBUG=0` |
| Open redirect | Django's `LoginView` only follows same-host `next` URLs |
| Malicious uploads | Pillow validates real image content, extension whitelist (no SVG), 10 MB limit, random file names, served only to logged-in users |
| Header injection | Download file names are sanitised |
| Weak config | The app refuses to start with `DJANGO_DEBUG=0` and the default secret key |

`python manage.py test` runs these checks in `accounts/test_security.py`.

> The lockout counters live in Django's cache. The default cache is per process, so if you
> run several worker processes, configure a shared cache (Redis or database).

Extra production variables: `DJANGO_SSL_REDIRECT` (default `1`), `DJANGO_HSTS_SECONDS`
(default `3600`), `DJANGO_BEHIND_PROXY=1` (trust `X-Forwarded-Proto` from your reverse proxy),
`DJANGO_LOGIN_MAX_ATTEMPTS`, `DJANGO_LOGIN_LOCKOUT_SECONDS`.

## Layout

```
webapp/
├── eds_web/        settings, root URLs
├── accounts/       admin-only user management, login signals, template tags
├── records/        EDSRecord + RecordHistory models, CRUD views, history helpers,
│                   import_legacy_db management command
├── templates/      Bootstrap 5 UI (sidebar layout, light/dark theme)
└── static/css/     app styles
```
