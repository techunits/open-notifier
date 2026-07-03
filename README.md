# eNotifier - Extendible Notifier System

**A self‑hosted, multi‑tenant notification engine with customizable template support (Email, WhatsApp, SMS).**

eNotifier is a Django service that sits between your applications and the many providers
that actually deliver messages (SMTP, SendGrid, Amazon SES, Mailchimp, Elastic Email, Mailtrap,
Brevo, Mailgun, Postmark, SendPulse, Interakt, …). Your apps call **one** stable API with a
*template reference* and a *data payload*;
eNotifier renders the template, picks the right provider for the tenant and channel,
delivers the message asynchronously, and records the outcome.

## The problem it solves

Most products end up re‑implementing the same notification plumbing over and over:

- **Provider lock‑in and churn.** Each email/WhatsApp/SMS vendor has its own SDK, auth scheme
  and payload shape. Wiring them directly into your app means vendor‑specific code scattered
  everywhere, and a painful migration every time you switch or add a provider.
- **Templates living in code.** Copy changes, new languages or a redesigned email shouldn't
  require a deploy. Non‑developers should be able to edit content safely.
- **Multi‑tenant fan‑out.** SaaS products need per‑customer sender identities, branding and
  provider credentials — not a single global config.
- **Reliability & visibility.** Sending inline blocks requests and hides failures. You need
  async delivery, retries and an auditable log of what was sent and whether it succeeded.

eNotifier centralises all of this behind a provider‑agnostic API so that **adding a
channel or swapping a vendor is a configuration change, not a code change**, and message
content is managed from a console instead of shipped in a release.

## How it works

1. **Tenants** isolate configuration and content per customer/product.
2. A **Template** (Django template syntax — `{{ var }}`, `{% if %}`) is stored per tenant and
   addressed by a stable `ref` key, so callers never hard‑code copy.
3. A **Configuration** binds a tenant + channel (`EMAIL` / `WHATSAPP` / `SMS`) to a specific
   **provider** and its credentials (`metadata`). One configuration per channel is marked
   `is_default` and used for delivery.
4. A client `POST`s a `template_ref` plus a data `payload` (and recipients) to the notification
   API. eNotifier renders the subject/body, creates a **NotificationLog**, and hands the
   job to a **Celery** worker.
5. The worker dispatches to the matching **integration** under
   `notifications/integrations/<provider>/sender.py`, which talks to the real vendor. The
   `NotificationLog` status moves `QUEUED → PROCESSING → SUCCESS / FAILED` for a full audit trail.

## Architecture at a glance

- **Framework:** Django 5.x / Django REST Framework, PostgreSQL for storage.
- **Async delivery:** Celery with a Redis broker; each send is a background task.
- **Pluggable providers:** drop a package under `notifications/integrations/` and it is
  auto‑discovered — no core changes required (see [Integrations](#integrations)).
- **Multiple entry points** (all share the same models and Celery pipeline):
  - **REST API** — the client‑facing notification API (below) and the console API.
  - **gRPC** — `python manage.py grpcserver` (via `django-grpc`) for high‑throughput callers.
  - **Socket.IO** — `python manage.py live_notify` for real‑time / live notifications.
- **Two admin surfaces:**
  - A modern, responsive **Webmaster Console** at `/notifier/webmaster-console/` for
    managing tenants, users, templates, configurations and integrations — documented below.
  - A **Docker Compose** topology (`web`, `grpc`, `celery`, `socketio`, PostgreSQL, Redis)
    for running the whole stack.

## Key features

- Multi‑tenant, per‑channel provider configuration with a `is_default` fallback.
- Provider‑agnostic API keyed by template `ref` — callers are decoupled from vendors.
- Server‑side template rendering with a visual (WYSIWYG) editor and live preview.
- Auto‑discovered, self‑describing integrations driven by a `MANIFEST` (form fields,
  validation, branding).
- Asynchronous delivery with a persisted, queryable delivery log.
- Ships with 12 bundled providers across Email and WhatsApp.

---

## Sending a notification (client API)

This is the API your applications call to actually send messages. It is scoped by tenant.

```
POST /notifier/tenants/<tenant_id>/notifications
GET  /notifier/tenants/<tenant_id>/notifications   # 25 most recent logs for the tenant
```

**Authentication.** Every client‑API request must carry a tenant **API key** in the
`Authorization` header — sent **verbatim, with no `Bearer` prefix**:

```
Authorization: enk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

The key must belong to the tenant in the URL. Keys are minted in the Webmaster Console
(**API Keys** page) — see [API keys](#api-keys). Failures: missing key →
`MISSING_API_KEY` (401), unknown/revoked → `INVALID_API_KEY` (401), past its expiry →
`EXPIRED_API_KEY` (401), key for a different tenant → `API_KEY_TENANT_MISMATCH` (403).

Example request body:

```jsonc
{
  "template_ref": "welcome_email",     // stable key of an enabled Template for the tenant
  "payload": { "name": "Ada", "plan": "Pro" },  // data for {{ variables }} (object or [{key,value}] list)
  "to":  ["ada@example.com"],          // Email recipients
  "cc":  [],
  "bcc": [],
  "to_numbers": ["+15551234567"]        // WhatsApp/SMS recipients
}
```

eNotifier looks up the template by `ref`, renders the subject and body with `payload`,
resolves the tenant's **default enabled Configuration** for each of the template's
`notification_types`, and enqueues delivery. The response returns the created log IDs:

```json
{ "notifications": [ { "id": "…uuid…" } ] }
```

If no matching default configuration exists for a channel, the request fails with
`NOTIFICATION_CONFIG_NOT_EXISTS` (HTTP 400).

---

## Webmaster Console

A standalone, responsive HTML webmaster console built with **Tailwind CSS** and **jQuery 4.0.0**
(both loaded from CDN — no build step required). It is implemented as the `en_console`
Django app and is compatible with **Django 5.x and 6.x**.

### What you can do

| Section | Capabilities |
|---|---|
| **Dashboard** | Live counters (tenants, users, templates, configurations, integrations) and recent notification logs with delivery health (success / failed / queued). |
| **Notification Logs** | A dedicated log of every notification with its delivery status, **filterable by status** (and by tenant). Each row opens a details view showing recipients, subject, template ref and the raw provider response. |
| **Tenants** | Create, edit, enable/disable and (soft) delete tenants. |
| **Users** | Create, edit and delete console users and assign a **role** + **associated tenants** (see [Roles & access control](#roles--access-control)). `TENANT_ADMIN`s manage only their scoped `CONFIG_ADMIN` / `DESIGN_ADMIN` users. Guards against deleting yourself or the last superuser. |
| **Email Templates** | A **visual template editor** with a WYSIWYG surface, raw HTML view, and a live server‑rendered preview. Manage subject, reference key, tenant, notification types, and `addon_data`. |
| **Configurations** | Manage per‑tenant delivery channels. The settings form is **driven by each provider's manifest**, so you only see the fields a provider actually needs. |
| **API Keys** | Mint, label, set expiry for, and revoke the per‑tenant keys that authenticate the client API. The raw key is shown **once** at creation (stored only as a hash). |
| **Integrations** | Auto‑discovers every provider under `notifications/integrations/`, shows its manifest, required config fields and how many configurations use it. `PLATFORM_ADMIN`s **enable/disable** each provider here (providers are disabled by default). |

### Visual template editor

The template editor (Email Templates → *New/Edit*) provides three synced views:

- **Visual** — an editable iframe (`designMode`) with a formatting toolbar
  (bold/italic/underline, headings, lists, links, colour).
- **HTML** — the raw template source for fine‑grained control.
- **Preview** — the template rendered **server‑side** with your sample data, so you see
  exactly what recipients get.

Extra helpers:

- **Insert `{{ variable }}`** at the cursor (works in both Visual and HTML views).
- **Detect variables** — scans the body + subject and builds a sample‑data JSON skeleton.
- Templates use **Django template syntax** (`{{ name }}`, `{% if %}` …), matching the
  rendering used by the notification senders.

### Access & security

- Authentication uses Django's session auth. A user can sign in **only if they resolve to a
  role** (see [Roles & access control](#roles--access-control)) — a Django superuser, or a
  user with an `en_console` **Membership**.
- The JSON API uses **DRF `SessionAuthentication` + role/capability permissions**, so every
  request is checked against the caller's role and **scoped to their associated tenants**, and
  every write is CSRF‑protected (the client sends `X-CSRFToken` automatically).
- Destructive actions are soft deletes (`is_deleted = True`) for tenants, templates and
  configurations; users are hard‑deleted (with safety guards).

### Roles & access control

The console is governed by a **four‑role** system. Every user has exactly one role, and the
tenant‑scoped roles are additionally tied to a set of **associated tenants** — stored as a
`Membership` row (`en_console/models.py`, one‑to‑one with the Django user + an M2M to
`Tenant`). Roles resolve in `en_console/roles.py`; both the JSON API and the sidebar are gated
by them, and **the API is the real boundary** — every query is scoped to the caller's tenants
regardless of what the UI shows.

The roles:

- **`PLATFORM_ADMIN`** — full access to everything, across all tenants. A Django **superuser is
  implicitly `PLATFORM_ADMIN`** even without a `Membership`.
- **`TENANT_ADMIN`** — full access, but only to its **associated tenants**. Cannot create or
  delete tenants (edit only), and when managing users may grant only `CONFIG_ADMIN` /
  `DESIGN_ADMIN`, and only within its own tenants.
- **`CONFIG_ADMIN`** — create/update/delete/list/view **configurations, integrations and
  templates**, plus **view notification logs**, for its associated tenants.
- **`DESIGN_ADMIN`** — create/update/delete/list/view **EMAIL templates** for its associated
  tenants (EMAIL‑only is enforced on the server). **No Dashboard** — it lands on the Email
  Templates page after login.

| Capability | PLATFORM_ADMIN | TENANT_ADMIN | CONFIG_ADMIN | DESIGN_ADMIN |
|---|:--:|:--:|:--:|:--:|
| Scope | All tenants | Associated tenants | Associated tenants | Associated tenants |
| Dashboard | ✅ | ✅ | ✅ | — |
| Notification Logs (view) | ✅ | ✅ | ✅ | — |
| Tenants | full CRUD | edit associated only | — | — |
| Users & roles | all roles | create/manage `CONFIG_ADMIN` / `DESIGN_ADMIN` in own tenants | — | — |
| Configurations | ✅ | ✅ | ✅ | — |
| API Keys | ✅ | ✅ | ✅ | — |
| Integrations (view) | ✅ | ✅ | ✅ | — |
| Templates (all types) | ✅ | ✅ | ✅ | — |
| **EMAIL** templates | ✅ | ✅ | ✅ | ✅ |

**Assigning roles.** On the **Users** page you set a user's **role** and **associated
tenants** — nothing else. Django's `is_staff` / `is_superuser` flags are **derived
automatically** and never shown: every console user is made staff, and choosing
`PLATFORM_ADMIN` also makes the user a Django superuser (choosing any other role clears it).
The same rule is enforced server‑side, so it holds for direct API calls too.

**Signing in.** A user can log in only if they resolve to a role (a superuser, or a user with
a `Membership`). Existing **non‑superuser** accounts without a `Membership` therefore have no
console access until a `PLATFORM_ADMIN` (or `TENANT_ADMIN`, within its scope) assigns them a
role. `GET api/me/` returns the signed‑in user's role, tenant scope, accessible pages and
derived capabilities — the UI uses it to hide what a role cannot do.

### API keys

The client API is authenticated with **per‑tenant API keys** (a `TenantApiKey`,
`tenants/models.py`). Managed on the **API Keys** console page by `PLATFORM_ADMIN`,
`TENANT_ADMIN` and `CONFIG_ADMIN` (scoped to their tenants), a tenant can hold **several**
keys for rotation.

- **One‑time reveal.** The raw key is returned only at creation and shown once in a dialog
  with a copy button; leaving that dialog requires confirming you've saved it. Afterwards the
  key is identified only by its **last 6 characters**.
- **Long by design.** Each raw key is **256 characters** (an `enk_` prefix + URL‑safe random
  filler), so it carries far more entropy than a brute‑force attack could ever cover.
- **Stored hashed.** Only a **SHA3‑512** (quantum‑resistant) hash of the key is persisted, so
  it can never be recovered — authentication re‑hashes the presented key and matches it.
- **Editable label** and an **expiry** chosen from `7 / 30 / 90 / 120 / 365 days` or *never*.
- **Revoke** deactivates a key immediately (any client using it starts getting `401`).

Send the key verbatim in `Authorization` (no `Bearer`) — see
[Sending a notification](#sending-a-notification-client-api).

---

## Integrations

An integration is any sub‑package of `notifications/integrations/<key>/` that contains a
`sender.py` (the worker that delivers a message). Add an optional `MANIFEST` dict in the
package's `__init__.py` to make it self‑describing for the webmaster console:

```python
# notifications/integrations/<key>/__init__.py
from .sender import send

MANIFEST = {
    "key": "smtp_email",            # must match the directory name
    "provider": "SMTP_EMAIL",       # must match Configuration.provider choice
    "name": "SMTP Email (SMTP)",    # display name
    "notification_type": "EMAIL",    # EMAIL | WHATSAPP | SMS
    "description": "…",
    "brand_color": "#0EA5E9",        # accent colour (optional)
    "logo": "<svg …></svg>",         # inline SVG badge shown in the UI (optional)
    "config_fields": [               # drives the Configuration form
        {"name": "smtp_host", "label": "SMTP Host", "type": "host", "required": True},
        {"name": "smtp_port", "label": "SMTP Port", "type": "number",
         "required": True, "default": 25, "min": 1, "max": 65535},
        {"name": "smtp_tls",  "label": "Use TLS",   "type": "boolean", "default": True},
        {"name": "api_key",   "label": "API Key",   "type": "password", "required": True,
         "pattern": r"^SG\..+", "pattern_message": "Must start with SG."},
        # type: text | host | url | number | password | email | boolean
        # extra keys: required (bool), default, placeholder, secret (bool),
        #             min/max (number), pattern + pattern_message (regex format)
    ],
}
```

The lowercased `provider` value must equal the package directory name — the same convention
already used by `notifications/tasks.py` to dispatch to a provider. Providers without a
`MANIFEST` still work and fall back to a generic raw‑JSON metadata editor.

**Provider‑settings editor.** On the Configurations page the "Provider settings" section is
generated from `config_fields` and offers an **AWS Secrets Manager–style toggle** between:

- **Key / value** — each metadata key as its own labelled, validated input, and
- **Plaintext (JSON)** — a raw JSON editor for the whole metadata object.

Switching between the two keeps values in sync (fields → JSON serialises the current
values; JSON → fields parses them back, and an invalid JSON blocks the switch with an
error). Either way the metadata is persisted **verbatim as raw JSON**.

**Provider‑settings validation.** Each field is validated against its manifest metadata
**both in the browser and on the server** (the API enforces the same rules via
`en_console/metadata.py`, so direct API calls — and the raw‑JSON editor — are validated too):

- `required` fields must be non‑empty.
- `number` fields must be whole numbers within `min`/`max` (e.g. SMTP port `1–65535`).
- `email` fields must be valid email addresses.
- `host` fields must be valid hostnames; `url` fields must be valid `http(s)` URLs.
- any field may declare a `pattern` (regex) + `pattern_message` for service‑specific
  formats (e.g. a SendGrid `SG.*` key, an AWS `AKIA…` access key, region `us-east-1`).

In the browser, invalid fields are highlighted and the errors listed inline before the
request is sent; the server returns them as `{"metadata": ["…"]}` with HTTP 400. The
metadata itself is stored verbatim as raw JSON on `Configuration.metadata` (declared
`number`/`boolean` fields are coerced to their proper JSON types). Each provider also shows
its logo across the Integrations and Configurations pages for quick visual identification.

Bundled integrations (email + WhatsApp):

| Directory | Provider | Channel | Delivery |
|---|---|---|---|
| `smtp_email` | `SMTP_EMAIL` | Email | Any standard SMTP server |
| `local_email` | `LOCAL_EMAIL` | Email | Local Postfix / MTA (127.0.0.1:25, no auth) |
| `sendgrid` | `SENDGRID` | Email | SendGrid v3 Mail Send API |
| `elastic_email` | `ELASTIC_EMAIL` | Email | Elastic Email v2 API |
| `mailchimp` | `MAILCHIMP` | Email | Mailchimp Transactional (Mandrill) API |
| `aws_ses` | `AWS_SES` | Email | Amazon SES API (needs `boto3`) |
| `mailtrap` | `MAILTRAP` | Email | Mailtrap Email Sending API |
| `brevo` | `BREVO` | Email | Brevo (formerly Sendinblue) v3 API |
| `mailgun` | `MAILGUN` | Email | Mailgun Messages API (needs sending `domain`) |
| `postmark` | `POSTMARK` | Email | Postmark Email API |
| `sendpulse` | `SENDPULSE` | Email | SendPulse SMTP API (OAuth2 client credentials) |
| `interakt` | `INTERAKT` | WhatsApp | Interakt Business API |
| `sample_email` | `SAMPLE_EMAIL` | Email | **Boilerplate template** — copy it to build your own |

### Enabling a provider

Providers are **disabled by default** — **except `SMTP_EMAIL`, which ships enabled** (it can
still be disabled by an admin). A disabled provider is discovered and shown on the console
**Integrations** page but **cannot deliver** — a notification routed to it is marked
`FAILED` with `"Provider <X> is disabled."`. A **`PLATFORM_ADMIN`** enables/disables a provider
with the toggle on that page (state is global, stored in `IntegrationState`); other roles see
a read‑only Enabled/Disabled badge. So the first‑run checklist for any provider is: create a
`Configuration` for a tenant → **enable the provider on Integrations** → send.

### Creating a new provider — step by step

A ready‑to‑copy template lives at `notifications/integrations/sample_email/`.

1. **Copy the package.** `cp -r notifications/integrations/sample_email notifications/integrations/<key>`
   where `<key>` is your provider's lowercase directory name (e.g. `postal`). The lowercased
   `provider` **must** equal `<key>` — that is how `notifications/tasks.py` locates the sender.
2. **Fill in the manifest** (`<key>/__init__.py`): set `key`, `provider` (UPPERCASE `<key>`),
   `name`, `notification_type`, `description`, optional `logo`/`brand_color`, and the
   `config_fields` that drive (and validate) the Configuration form. Keep this file free of
   heavy imports. *No model edit or migration needed* — `PROVIDER_STATUS_CHOICES` is
   auto‑discovered from the filesystem at startup, so the provider registers itself.
3. **Implement `send(notification_id)`** (`<key>/sender.py`): read credentials from
   `config_obj.metadata`, the rendered message from `notification_obj.metadata`
   (`subject`, `body`, `to`/`cc`/`bcc`), call your provider, and move the log to
   `SUCCESS`/`FAILED` with the response under `metadata["response"]`. It is a `@shared_task`,
   auto‑registered with Celery via `autoload_senders()`.
4. **Add any dependency** to `requirements.txt` (import it at the top of `sender.py`, never in
   `__init__.py`).
5. **Restart** the app + Celery worker (so the new package is discovered), then
   **enable the provider** on the Integrations page and create a `Configuration` for a tenant.

---

## Webmaster Console API

Base path: `/notifier/webmaster-console/api/`
Auth: session cookie of a staff user. Unsafe methods require the `X-CSRFToken` header.
All responses are JSON. Errors use `{"error": {"ref": "...", "message": "..."}}` where applicable.

### Pages (HTML)

| URL | Description |
|---|---|
| `GET /notifier/webmaster-console/` | Dashboard |
| `GET /notifier/webmaster-console/login/` · `POST` | Sign in |
| `GET /notifier/webmaster-console/logout/` | Sign out |
| `GET /notifier/webmaster-console/logs/` | Notification Logs page (status filter) |
| `GET /notifier/webmaster-console/tenants/` | Tenants page |
| `GET /notifier/webmaster-console/users/` | Users page |
| `GET /notifier/webmaster-console/templates/` | Templates page (visual editor) |
| `GET /notifier/webmaster-console/configurations/` | Configurations page |
| `GET /notifier/webmaster-console/apikeys/` | API Keys page |
| `GET /notifier/webmaster-console/integrations/` | Integrations page |

### Meta & dashboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `api/meta/` | Choice lists: `notification_types`, `providers`, `notification_statuses`, `roles`. |
| `GET` | `api/me/` | The signed‑in user's `role`, tenant scope, accessible `pages` and `caps`. |
| `GET` | `api/stats/` | Dashboard counters + 10 most recent notification logs (scoped to the caller's tenants). |

### Tenants

| Method | Endpoint | Body / Notes |
|---|---|---|
| `GET` | `api/tenants/` | List (excludes soft‑deleted). |
| `POST` | `api/tenants/` | `{ "name", "is_enabled" }` |
| `GET` | `api/tenants/<uuid>/` | Retrieve. |
| `PUT/PATCH` | `api/tenants/<uuid>/` | Update. |
| `DELETE` | `api/tenants/<uuid>/` | Soft delete. |

### Users

| Method | Endpoint | Body / Notes |
|---|---|---|
| `GET` | `api/users/` | List. |
| `POST` | `api/users/` | `{ "username", "email", "first_name", "last_name", "password", "is_active", "role", "tenants": [uuid…] }` — `is_staff` / `is_superuser` are derived from `role`. |
| `GET` | `api/users/<int>/` | Retrieve. |
| `PUT/PATCH` | `api/users/<int>/` | Update (omit `password` to keep current). |
| `DELETE` | `api/users/<int>/` | Hard delete (blocked for self / last superuser). |

### Email Templates

| Method | Endpoint | Body / Notes |
|---|---|---|
| `GET` | `api/templates/?tenant=<uuid>` | List (optional tenant filter). |
| `POST` | `api/templates/` | `{ "tenant", "name", "ref", "subject", "notification_types": ["EMAIL"], "body", "addon_data", "is_enabled" }` |
| `POST` | `api/templates/preview/` | `{ "body", "subject", "payload" }` → server‑rendered `{ "subject", "body" }`. |
| `GET` | `api/templates/<uuid>/` | Retrieve. |
| `PUT/PATCH` | `api/templates/<uuid>/` | Update. |
| `DELETE` | `api/templates/<uuid>/` | Soft delete. |

### Configurations

| Method | Endpoint | Body / Notes |
|---|---|---|
| `GET` | `api/configurations/?tenant=<uuid>` | List (optional tenant filter). |
| `POST` | `api/configurations/` | `{ "tenant", "notification_type", "provider", "metadata": {...}, "is_default", "is_enabled" }` |
| `GET` | `api/configurations/<uuid>/` | Retrieve. |
| `PUT/PATCH` | `api/configurations/<uuid>/` | Update. |
| `DELETE` | `api/configurations/<uuid>/` | Soft delete. |

### Integrations

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `api/integrations/` | All discovered manifests + `configuration_count` and `is_enabled` per provider. |
| `GET` | `api/integrations/<key>/` | A single manifest + the configurations using it. |
| `PATCH` | `api/integrations/<key>/` | `{ "is_enabled": true\|false }` — enable/disable the provider (`PLATFORM_ADMIN` only). |

### API Keys

| Method | Endpoint | Body / Notes |
|---|---|---|
| `GET` | `api/apikeys/?tenant=<uuid>` | List keys (never returns the raw key or hash). |
| `POST` | `api/apikeys/` | `{ "tenant", "label", "expires_in_days": 7\|30\|90\|120\|365\|null }` → returns the key **once** as `api_key`. |
| `PATCH` | `api/apikeys/<uuid>/` | `{ "label" }` — rename only. |
| `DELETE` | `api/apikeys/<uuid>/` | Revoke (deactivate; the key stops authenticating immediately). |

### Notification Logs (read-only)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `api/logs/` | Delivery log, newest first (capped at the 500 most recent). |
| `GET` | `api/logs/?status=<STATUS>` | Filter by status: `QUEUED` · `PROCESSING` · `SUCCESS` · `FAILED`. |
| `GET` | `api/logs/?tenant=<uuid>` | Filter by tenant (combines with `status`). |

Each entry includes `status`, `tenant_name`, `provider`, `notification_type`, `template_ref`,
`created_on` and the full `metadata` (recipients, subject, and the provider `response`).

---

## Running locally

```sh
# install dependencies
pip install -r requirements.txt

# migrate + load demo data + collect static (see bootstrap.sh)
python manage.py migrate
python manage.py loaddata notifier/misc/fixtures/auth.json \
                          notifier/misc/fixtures/tenants.json \
                          notifier/misc/fixtures/configurations.json \
                          notifier/misc/fixtures/templates.json

# run
python manage.py runserver
```

Then open the webmaster console at: <http://localhost:8000/notifier/webmaster-console/>

### Default admin credentials

```
admin@enotifier.techunits.com / password
```

> **Note:** the admin panel loads Tailwind and jQuery from CDN. Tailwind's Play CDN is
> intended for development/prototyping; for a hardened production deployment, pin a built
> Tailwind stylesheet and a self‑hosted jQuery 4.0.0 build.
