# EMASA Platform: Monitor $backend$ 😊

[]()
<a name=""></a>


- [EMASA Platform: Monitor $backend$ 😊](#emasa-platform-monitor-backend-)
  - [Environment variables](#environment-variables)
    - [DB Prefix usage ](#db-prefix-usage-)
    - [Default .env template](#default-env-template)
  - [Backend setup](#backend-setup)
    - [Windows](#windows)
    - [Linux](#linux)
  - [API Docs (Swagger, ReDoc)](#api-docs-swagger-redoc)
  - [Authentication with EchoAPI](#authentication-with-echoapi)
    - [Get tokens:](#get-tokens)
    - [Refresh tokens](#refresh-tokens)
    - [Token usage](#token-usage)
  - [Custom Permission classes](#custom-permission-classes)
    - [HasPermissionKey](#haspermissionkey)
    - [IsAdminOrIsAuthenticatedReadOnly](#isadminorisauthenticatedreadonly)
  - [Seed data](#seed-data)
    - [Administration json](#administration-json)
    - [Infrastructure json](#infrastructure-json)
  - [Special Methods](#special-methods)
    - [Automatic Key creation method](#automatic-key-creation-method)
    - [Coming soon](#coming-soon)


## <a name="env_var">Environment variables</a>

| Name          | Description                                          |
| ------------- | ---------------------------------------------------- |
| DEBUG         | Default=False                                        |
| SECRET_KEY    | Django's secret key                                  |
| DATABASE_URL  | Url for the used database                            |
| ALLOWED_HOSTS | If you're testing, you can write here your localhost |
| DB_PREFIX     | Prefix used in the naming of the DB tables           |

### <a name="db_prefix">DB Prefix usage </a>

(UPDATE) Just add it to your .env, can be whatever you need it to be. (Make sure you name it something like `your_prefix_` end it with a "_")

### <a name="env_template">Default .env template</a>

This file should be created where your manage.py file is located, **please don't forget to modify the fields according to your needs**.

```ini
DEBUG=True 
SECRET_KEY=your_secret_key
DATABASE_URL=postgres://user:password@localhost:5432/test_db # Adjust this to your needs, if it doesn't work, change postgres for postgresql or your port, check the docker-compose.yml file
DB_PREFIX=test_monitor_ # See DB Prefix usage for more information
ALLOWED_HOSTS=127.0.0.1, localhost
```


## <a name="setup">Backend setup</a>

This is a guide step by step to set up the backend in your environment.
1. Setup the database with docker, you can use the `docker-compose.yml` file, but change the ports if you are already using those or if you don't like 5432 number, it can happen and I get it, it's an ugly number 😠.
1. Make sure you're using python 3.12+ ‼️
1. Clone this repository in a directory of your preference📂, it's important for you to use the `backend` branch.
    https://github.com/Jonathan-GC/EMASA-platform.git
1. Create a virtual environment where this `README.md` is located and activate it.
---
### Windows
```bash
python -m venv venv
```
```bash
venv\Scripts\activate
```
Note: Rename the virtual environment if you like, or just copy and paste those up here ⬆️.
### Linux
```bash
python3 -m venv venv
```
```bash
source venv/bin/activate
```
---
5. Now, install the `requirements.txt`
```bash
pip install -r requirements.txt
```
6. Try to use the django shell to make sure everything is working. Otherwise you might need to pull again or report this issue.
```bash
python manage.py shell
```
7. If everything is fine, proceed with migrating. First makemigrations, to make sure there's no pending migrations to make, then migrate.
```bash
python manage.py makemigrations && python manage.py migrate
```
8. Then, and only then, load the seed data to the database see [seed data](#seed-data) for more info 😊
```bash
python manage.py loaddata fixtures/administration.json && python manage.py loaddata fixtures/infrastructure.json && python manage.py loaddata fixtures/keys.json
```
9. Now, run it :v
```bash
python manage.py runserver
```
Note: at this point, if you get the allowed hosts error, check if your .env is working.

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

<"diagram pic">

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

This data is for developing purposes only! ‼️‼️‼️

Contained in the json files located in 📂fixtures, it's a set test data.

### Administration json

Contains mostly administration purposes data:

|Type|Quantity|
|----|----|
|Region| 1|
|Superuser|1|
|Organizations|2|
|Roles|4|
|Workspaces|3|
|Users|4|
|Permission Keys| A LOT|

User account/pass relation classified by role, organization and workspace:

|User|Password|Organization|Role|Workspace|
|---|---|---|---|---|
|weedo|estrellita123|None|superuser|None|
|emasa_admin|estrellita123|EMASA|Admin|Principal|
|emasa_employee|estrellita123|EMASA|Sin rol|Principal|
|tec_admin|estrellita123|Tecnobot|Admin|Principal|
|tec_employee|estrellita123|Tecnobot|Sin rol|Principal|

1 Additional workspace: Tecnobot (emasa side).

### Infrastructure json

Infrastructure seed data

|Type|Quantity|
|---|---|
|Machines|4|
|Services|4|
|Nodes|8|
|Gateways|4|
|NodeTypes|4|

## Special Methods

This is a list of special methods and endpoints (☝️🤓 Implemented), it details each method or endpoint with it's usage and purposes.

### Automatic Key creation method

Implemented with a Mixin: PermissionKeyMixin. This mixin creates any basic key for a new object that it's viewset **uses** this mixin. Basic keys includes basic actions: get, get_by_id, etc... It uses bulk create, so it doesn't uses the PermissionKey's model save() method, so, this mixin takes care of the automatic code attribute set. This could leave the save() method obsolete, but we'll see. 

NOTE: This method doesn't need an endpoint.

### Coming soon

...