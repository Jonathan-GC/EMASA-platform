# EMASA Platform: Monitor $backend$ 😊

[]()
<a name=""></a>


- [EMASA Platform: Monitor $backend$ 😊](#emasa-platform-monitor-backend-)
  - [Environment variables](#environment-variables)
    - [Django Settings](#django-settings)
    - [PostgreSQL Database Settings](#postgresql-database-settings)
    - [Database Prefix](#database-prefix)
    - [DB Prefix usage ](#db-prefix-usage-)
    - [Default .env template](#default-env-template)
  - [Backend setup](#backend-setup)
  - [API Docs (Swagger, ReDoc)](#api-docs-swagger-redoc)
  - [Authentication with EchoAPI](#authentication-with-echoapi)
    - [Get tokens:](#get-tokens)
    - [Refresh tokens](#refresh-tokens)
    - [Token usage](#token-usage)
  - [Custom Permission classes](#custom-permission-classes)
    - [HasPermissionKey](#haspermissionkey)
    - [IsAdminOrIsAuthenticatedReadOnly](#isadminorisauthenticatedreadonly)
  - [Seed data](#seed-data)
  - [Special Methods](#special-methods)
    - [Automatic Key creation method](#automatic-key-creation-method)
    - [Automatic group creation method](#automatic-group-creation-method)


## <a name="env_var">Environment variables</a>

The following environment variables are used to configure the application:

### Django Settings

* `DJANGO_DEBUG`: Enables debug mode for the Django application. Set to `1` to enable.
* `DJANGO_SECRET_KEY`: Secret key for the Django application. **Must be changed to a unique and secret value**.
* `DJANGO_ALLOWED_HOSTS`: Comma-separated list of allowed hosts for the Django application. Set to `*` to allow all hosts.

### PostgreSQL Database Settings

* `POSTGRES_DB`: Name of the PostgreSQL database.
* `POSTGRES_USER`: Username for the PostgreSQL database.
* `POSTGRES_PASSWORD`: Password for the PostgreSQL database.
* `POSTGRES_HOST`: Hostname or IP address of the PostgreSQL database.
* `POSTGRES_PORT`: Port number for the PostgreSQL database.

### Database Prefix

* `DB_PREFIX`: Prefix for the database tables. Set to `monitor_test_` for testing purposes.

**Note**: These environment variables are used to configure the application and should be set accordingly. The `DJANGO_SECRET_KEY` should be kept secret and not committed to version control.

### <a name="db_prefix">DB Prefix usage </a>

(UPDATE) Just add it to your .env, can be whatever you need it to be. (Make sure you name it something like `your_prefix_` end it with a "_")

### <a name="env_template">Default .env template</a>

This file should be created where your manage.py file is located, **please don't forget to modify the fields according to your needs**.

```ini
DJANGO_DEBUG=1
DJANGO_SECRET_KEY=switch-to-a-super-secret-one
DJANGO_ALLOWED_HOSTS=*

POSTGRES_DB=appdb
POSTGRES_USER=appuser
POSTGRES_PASSWORD=apppass
POSTGRES_HOST=db
POSTGRES_PORT=5432
DB_PREFIX=monitor_test_
```


## <a name="setup">Backend setup</a>

This is a guide step by step to set up the backend in your environment.
1. Clone the repository (if from scratch) and checkout to branch **feature/backend**, just in case if this isn't in the main branch yet. If not from scratch, pull and checkout.
2. Give permissions to the `entrypoint.sh` file, just in case:
```bash
sudo chmod +x entrypoint.sh
```
3. Locate with your terminal the `docker-compose.yml` and enter this command:
```bash
sudo docker compose build
```
And when it's done:
```bash
sudo docker compose up -d
```
1. Check if everything went right with:
```bash
sudo docker compose logs -f django_backend
```

Next step will be **login** to **/admin/** and check everything.

## <a name="docs">API Docs (Swagger, ReDoc)</a>

For endpoints or API Docs you can access `/api/schema/swagger-ui/` for swagger or `/api/schema/redoc/`. 

## <a name="auth">Authentication with EchoAPI</a>

There's an *📂Auth* folder in EchoAPI's: **📂Monitor | Emasa**. There you can found 2 elements: *Get tokens* and *Refresh Token*. Make sure the server is running (`python3 manage.py runserver`)

### Get tokens:

In Get Tokens: replace username and pasword in Body > raw with the username and password you created during the instalation with `createsuperuser`, if you don't remember that combination, repeat that step and just create another user.

```json
    {
        "username": "your_username",
        "password": "your_password"
    }
```
Send the request, the result should be 2 tokens: Access token, Refresh token. Acording to our settings.py jwt config, access token are only valid for 20 minutes, you'll have to auth again or proceed with **Refresh token**⬇️.

### Refresh tokens

In Refresh Tokens: replace refresh in Body > raw with your refresh token.

```json
    {
    "refresh":"your_refresh_token"
    }
```
The result should be a new access token.

### Token usage

In any request you want to make (eg. `infrastructure_api_v1_node_list`) go to Auth set *Type* to "Bearer token" and paste your access token in the *Token* textfield, make sure the token is new or not expired. The result, depending on the user you got the token with (permissions), should be 200 OK.

## <a name="perms">Custom Permission classes</a>

### HasPermissionKey

This permission class is located in `roles.permissions` if you acces it from any other app, if you are trying to import this class in roles app, you can just use `.permissions`.

This class has two parts, one function (`has_permission()`) and the class itself (`HasPermissionKey`). It's based on a RBAC (Role Based Access Control), that you can see as "keychains", a keychain equals a role and each key equals an action that a role can perform.

In this case, we use a model called PermissionKey, which contains three relevant parts to this manner: the scope, the entity and the action. When you create a key, it follows this naming structure: `<scope>:<entity_id>:<action>` (e.g. `node:22:get`). It connects to the user through `WorkspaceMembership`, `Role` and `RolePermission`. `RolePermission` stores `Role` and it's `PermissionKey`, and `WorkspaceMembership` stores `User`,`Role` and `Workspace`.

<iframe width="768" height="496" src="https://miro.com/app/live-embed/uXjVJat8v5k=/?focusWidget=3458764635787706402&embedMode=view_only_without_ui&embedId=331675989933" frameborder="0" scrolling="no" allow="fullscreen; clipboard-read; clipboard-write" allowfullscreen></iframe>

To use this permission class, you have to make sure to put it in your viewset, in `permission_classes`, it already includes `IsAuthenticated` and `IsAdminUser` permissions. 

 - Example
```python
class GatewayViewSet(viewsets.ModelViewSet):
    queryset = Gateway.objects.all()
    serializer_class = GatewaySerializer
    permission_classes = [HasPermissionKey] # Here, no need for IsAdminUser or IsAuthenticated
```
NOTE: you have to verify the context of the viewset. (e.g. You don't need a key for `PermissionKey`, in that case you use `IsAdminUser` and `IsAuthenticated`.)

### IsAdminOrIsAuthenticatedReadOnly

Returns True if the user has permission to access the view based on the request method and the user's authentication status. The permission rules are as follows:

    - GET, HEAD, OPTIONS requests are allowed if the user is authenticated.
    - POST, PUT, PATCH, DELETE requests are allowed if the user is a superuser.

Otherwise, the method returns False, permission wil be denied.

## Seed data

This seed data is for developing purposes only! ‼️‼️‼️

Contained in the json files located in 📂fixtures, it's a set test data. It is structured to work along with uplinks and downlinks in chirpstack. The data loaded contains every basic model for testing and frontend purposes.

User account/pass relation classified by role, organization and workspace:

|User|Password|Organization|Role|Workspace|
|---|---|---|---|---|
|weedo|estrellita123|None|superuser|None|
|emasa_admin|estrellita123|EMASA|Admin|Principal|
|emasa_employee|estrellita123|EMASA|Sin rol|Principal|
|tec_admin|estrellita123|Tecnobot|Admin|Principal|
|tec_employee|estrellita123|Tecnobot|Sin rol|Principal|

## Special Methods

This is a list of special methods and endpoints (☝️🤓 Implemented), it details each method or endpoint with it's usage and purposes.

### Automatic Key creation method

Implemented with a Mixin: PermissionKeyMixin. This mixin creates any basic key for a new object that it's viewset **uses** this mixin. Basic keys includes basic actions: get, get_by_id, etc... It uses bulk create, so it doesn't uses the PermissionKey's model save() method, so, this mixin takes care of the automatic code attribute set. This could leave the save() method obsolete, but we'll see. 

NOTE: This method doesn't need an endpoint.

### Automatic group creation method

For usable purposes, it's not needed to manually create a group through django's shell or django admin, when you create a Tenant, the `group` attribute will correspond to the name of the group automatically created, so, make sure to get this right.

...