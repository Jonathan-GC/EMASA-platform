# Hall Pass Workspace Visibility Fix

Branch: `fix/hall-pass-workspace-visibility`
Delivery: single-pr
Test runner: `python manage.py test`
Forecast: ~60 authored changed lines

## Specs

- S1: "hall pass is not granting read access or showing up in the objective workspace"
- S2: "not showing up when the user who owns the hall pass lists workspaces without the tenant or workspace headers"
- S3: "can't see the workspaces with or without the headers"
- S4: "tried to list services without the header and still can't read"
- S5: "it is supposed to show up when this user gets the workspace queryset"

## Tasks

- T1 (S1,S2,S3,S5) inline — WorkspaceViewSet.get_queryset: union pass-covered workspaces into queryset and bypass tenant filter for them
- T2 (S3) inline — TenantContextMiddleware: add hall pass awareness to is_authorized check so pass holders can access the target tenant
- T3 (S1-S5) inline — Tests: add focused tests covering hall pass workspace visibility and middleware pass-through

## Log

- L1: "I need to figure out why the hall pass is not granting read access or showing up in the objective workspace its not showing up when the user who owns the hall pass lists workspaces without the tenant or workspace headers, im checking the request im making, can't see the workspaces with or without the headers, it is supposed to show up when this user gets the workspace queryset. I also tried to list services without the header and still can't read."
