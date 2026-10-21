# Proposal: Core Multitenancy

## Why
Eliminate hardcoded tenant checks (e.g. "Monitor" string in organizations/views.py), decouple rigid User->Tenant foreign key to support multi-tenant user memberships and clean tenant transitions without permission residue or data corruption.

## What Changes
### In Scope
- **Master Tenant Formalization**: Replace hardcoded tenant checks with `Tenant.is_global` and platform settings.
- **Multi-tenant User Memberships**: Evolve `UserBase.tenant` into a flexible membership model with active tenant context and primary tenant while retaining backward compatibility.
- **User Tenant Lifecycle & Transfer**: Dedicated service and endpoint to safely transfer users between tenants, cleaning up prior workspace memberships, groups, and permissions.
- **ChirpStack Tenant Consistency**: Preserve ChirpStack synchronization during user and tenant operations.

### Out of Scope
- Dynamic permissions catalog and UI dynamic RBAC (SDD 2).
- Support ticket permission scoping and cross-tenant technician dispatch (SDD 3).

## Capabilities
### New Capabilities
- tenant-isolation: Formal Master Tenant rules and contextual tenant resolution.
- tenant-membership-transfer: Clean user lifecycle and migration across tenants with audit logs.

### Modified Capabilities
- None

## Approach
- Add `is_global` boolean flag to `Tenant` model to explicitly designate master tenants, replacing string-matching checks like `"Monitor"`.
- Introduce tenant membership management allowing users to associate across tenants while preserving `UserBase.tenant` as default/active tenant context.
- Implement transactional transfer service that cleanly revokes prior tenant-bound groups, object permissions, and workspaces before establishing new tenant associations.
- Maintain ChirpStack tenant consistency via synchronized API updates during user creation and transfer.

## Affected Areas
- `Monitor_Atlas/users/models.py`
- `Monitor_Atlas/organizations/models.py`
- `Monitor_Atlas/organizations/views.py`
- `Monitor_Atlas/roles/helpers.py`
- `Monitor_Atlas/users/serializers.py`
- `Monitor_Atlas/users/views.py`

## Risks
- **Data Inconsistency during Transfer**: Concurrent operations could leave orphaned permissions. *Mitigation*: Execute transfers within atomic database transactions with pre-validation.
- **Backward Compatibility**: Existing queries relying directly on `user.tenant`. *Mitigation*: Retain `user.tenant` as active tenant context delegating to membership.
- **ChirpStack Desynchronization**: External API failure during migration. *Mitigation*: Wrap ChirpStack calls in compensation and idempotency guards.

## Rollback Plan
- Revert schema migrations using Django migration rollback (`python manage.py migrate <app> <prev_migration>`).
- Revert codebase changes via Git.
- Restore ChirpStack tenant associations from transfer audit logs if external drift occurs.

## Dependencies
- Django ORM and migrations.
- ChirpStack v4 API integration.
- Existing `organizations` and `roles` permission helpers.

## Success Criteria
- Zero occurrences of hardcoded tenant string checks (e.g. `"Monitor"`).
- User tenant transfers purge all previous tenant permissions and memberships without data residue.
- Multi-tenant contextual resolution returns correct tenant scope for all requests.
- ChirpStack tenant state remains synchronized after transfers.
- Unit and integration tests pass without regression.
