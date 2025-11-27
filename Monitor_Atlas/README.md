# EMASA Platform: Monitor $Atlas API$ 🌎

[]()
<a name=""></a>


- [EMASA Platform: Monitor $Atlas API$ 🌎](#emasa-platform-monitor-atlas-api-)
  - [Deployment config](#deployment-config)
    - [Django Settings](#django-settings)
    - [PostgreSQL Database Settings](#postgresql-database-settings)
    - [Other important environment variables](#other-important-environment-variables)
    - [DB Prefix usage ](#db-prefix-usage-)
  - [Backend setup](#backend-setup)
  - [API Docs (Swagger, ReDoc)](#api-docs-swagger-redoc)
  - [Authentication with Apidog, Postman and such](#authentication-with-apidog-postman-and-such)
    - [Login:](#login)
    - [Refresh](#refresh)
    - [Token usage](#token-usage)
  - [Seed data](#seed-data)


## Deployment config

The following environment variables are used to setup the app:

### Django Settings

* `DJANGO_DEBUG`: Enables debug mode for the Django application. Set to `1` to enable `0` to disable.
* `DJANGO_SECRET_KEY`: Secret key for the Django application. **Must be changed to a unique and secret value** you can generate a new secure & unique one with: 
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

* `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts for the Django application. Set to `*` to allow all hosts in development. It's important to change this if you're on production, check your host or vps address and add it.

### PostgreSQL Database Settings

* `POSTGRES_DB`: Name of the PostgreSQL database.
* `POSTGRES_USER`: Username for the PostgreSQL database.
* `POSTGRES_PASSWORD`: Password for the PostgreSQL database.
* `POSTGRES_HOST`: Hostname or IP address of the PostgreSQL database.
* `POSTGRES_PORT`: Port number for the PostgreSQL database.
* `DB_PREFIX`: Use this to prefix the name of the DB tables if needed (see [DB Prefix usage](#db_prefix)).

**Note**: These environment variables are used to configure the application and should be set accordingly. The `DJANGO_SECRET_KEY` should be kept secret and not committed to version control.

### Other important environment variables

The following environment variables used in the project are described below (name — purpose — example / notes):

- `CHIRPSTACK_BASE_URL` — Base URL of the ChirpStack API (LoRa integration). Example: `http://192.168.0.169:8090/api`.
- `CHIRPSTACK_JWT_TOKEN` — JWT token used to authenticate with the ChirpStack API.
- `APP_URL` — Main application domain; used to build links in emails, redirects and some callbacks. In development it can be `http://localhost:5173`; in production it can be the public domain (e.g. `https://mtr-online.com`).
- `MTR_LOGO_URL` — Public URL of the logo used in emails and email templates (Mailgun). Example: `https://.../logo.png`.
- `HERMES_WS_URL` — WebSocket connection URL for the Hermes service (e.g. `ws://localhost:5000` or `wss://hermes.mydomain.com`). Hermes is the WebSocket API used for real-time events between services.
- `HERMES_API_URL` — HTTP/REST endpoint for Hermes (for non-WS calls to the Hermes service).
- `SERVICE_API_KEY` — Shared secret key to authorize communication between Hermes and Atlas (and other internal services). Treat it as a secret and do not commit it to the repository.
- `WS_SECRET` — Secret used to sign/validate WebSocket messages or WS-related tokens.
- `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `MAILGUN_FROM` — Configuration required to send emails via Mailgun. `MAILGUN_FROM` usually has the format `"Name <no-reply@domain.com>"`.
- `GOOGLE_CLIENT_ID`, `GOOGLE_SECRET` — Credentials to enable Google OAuth (Sign in with Google).
- `ACCESS_TOKEN_DURATION` — Access token duration in minutes (SIMPLE_JWT uses `timedelta(minutes=...)`). Example in `.env`: `60` (60 minutes).
- `REFRESH_TOKEN_DURATION` — Refresh token duration in days (SIMPLE_JWT uses `timedelta(days=...)`). Example in `.env`: `1` (1 day).
- `REFRESH_COOKIE_NAME`, `REFRESH_COOKIE_PATH` — Name and path of the cookie used for refresh tokens (defaults set in `settings.py`).
- `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_CREDENTIALS` — Allowed origins for CORS and whether credentials are allowed; separate multiple origins with commas in the `.env`.
- `CSRF_TRUSTED_ORIGINS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `CSRF_COOKIE_SAMESITE`, `COOKIE_SECURE` — Settings related to cookie and CSRF security. In development these are typically `false` and `Lax`; in production set to `true` and adjust `SameSite` according to your domain.

Quick tips:
- For local development you can leave `APP_URL` pointing to `http://localhost:5173` and `HERMES_WS_URL` to `ws://localhost:5000`.
- Keep `SERVICE_API_KEY`, `WS_SECRET`, `DJANGO_SECRET_KEY` and Mailgun/Google keys out of version control (use CI/CD secrets or server environment variables).
- `ACCESS_TOKEN_DURATION` is interpreted in minutes; `REFRESH_TOKEN_DURATION` is interpreted in days.

### <a name="db_prefix">DB Prefix usage </a>

(UPDATE) Just add it to your .env, can be whatever you need it to be. (Make sure you name it something like `your_prefix_` end it with a "_")


## <a name="setup">Backend setup</a>

This is a guide step by step to set up the backend in your environment.
1. Clone the repository (if from scratch) and checkout to branch **feature/backend**, just in case if this isn't in the main branch yet. If not from scratch, pull and checkout.
2. Give permissions to the `initial_setup.sh`, `entrypoint.sh`, `chirpstack_sync.sh` files, if using linux:
```bash
sudo chmod +x entrypoint.sh
sudo chmod +x initial_setup.sh
sudo chmod +x chirpstack_sync.sh
```
3. In the same directory `Monitor_Atlas/` where the `docker-compose.yml` is located, enter this command:
```bash
sudo docker compose up --build -d
```
4. Check if everything went right with:
```bash
sudo docker compose logs -f django_backend
```
Default por for the Atlas API is `8000`.

## <a name="docs">API Docs (Swagger, ReDoc)</a>

For endpoints auto schema or API Docs you can access `/api/schema/swagger-ui/` for swagger or `/api/schema/redoc/` powered by `drf-spectacular` 😊. 

## <a name="auth">Authentication with Apidog, Postman and such</a>

( $Apidog$ )There's an *📂Auth* folder in Apidog's: **📂Atlas API | Monitor**. There you can found 2 endpoints: *Login* and *Refresh*. Make sure the server is running. Check the body and hit send.

### Login:

In Login: replace username and pasword in Body > raw with the username and password (check seed data).

```json
    {
        "username": "your_username",
        "password": "your_password"
    }
```
Send the request, the response should be 2 tokens: Access token, Refresh token. Refresh token is set as a cookie, access token must be stored in session storage or local storage. Acording to our settings.py jwt config, access token are only valid for 20 minutes, you'll have to auth again or proceed with **Refresh token**⬇️.

### Refresh

In Refresh Tokens: replace refresh in Body > raw with your refresh token.

```json
    {
    "refresh":"your_refresh_token"
    }
```
The result should be a new access token and a new refresh token since there is token blacklisting.

### Token usage

In any request you want to make (eg. `Application list`) go to Auth set *Type* to "Bearer token" and paste your access token in the *Token* textfield or set it as a variable (its already done, check apidog's docs for variable setting and usage), make sure the token is new or not expired. The result, depending on the user you got the token with (permissions), should be 200 OK.


## Seed data

The fixtures under the `fixtures/` folder provide development seed data used by the project. The table below lists the user accounts included in the current fixtures (only these accounts are present). The plaintext password for all seeded users is: `estrellita123`.

All accounts belong to the organization "Monitor" and the main workspace "Principal".

| Username              | Password      | Organization | Role       | Workspace |
| --------------------- | ------------- | ------------ | ---------- | --------- |
| monitor.administrador | estrellita123 | Monitor      | Admin      | Principal |
| monitor.gerente_1     | estrellita123 | Monitor      | Manager    | Principal |
| monitor.technician_1  | estrellita123 | Monitor      | Technician | Principal |
| monitor.viewer_1      | estrellita123 | Monitor      | Viewer     | Principal |
| support.manager       | estrellita123 | Monitor      | Support    | Principal |
| support_agent_1       | estrellita123 | Monitor      | Support    | Principal |
| support_agent_2       | estrellita123 | Monitor      | Support    | Principal |
| support_technician_1  | estrellita123 | Monitor      | Support    | Principal |
| support_technician_2  | estrellita123 | Monitor      | Support    | Principal |

