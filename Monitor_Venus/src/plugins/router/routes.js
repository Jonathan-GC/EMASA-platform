import { paths as P } from './paths'
import { components as C, components } from './components'
import { parameters as V } from './parameters';
import { 
    requireAuth, 
    requireGuest, 
    allowAll,
    requireSuperUser,
    requireAdmin,
    requireNormalUser,
    requireManager,
    requireTechnician,
    requireViewer,
    requireTenantUser,
    requireRoles,
    requireTenant
} from "@utils/auth/guards.js";


export const routes = [

    { path: '/', redirect: P.LOGIN },
    {
        path: P.ROOT,
        component: C.DEFAULT_LAYOUT,
        children: [
            {
                path: P.HOME,
                component: C.HOME,
                meta: { 
                    requiresAuth: true,
                    label: 'Home'
                }
            },
            {
                path: P.ABOUT,
                component: C.ABOUT,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    label: 'About'
                }
            },
            // ========================================
            // RUTAS DE ADMINISTRACIÓN
            // Solo SuperUsers y Admins
            // ========================================
            {
                path: P.TENANTS,
                component: C.TENANTS,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    roles: ['root', 'admin'],
                    label: 'Tenants'
                }
            },
            /*{
                path: P.TENANT_MANAGERS,
                component: C.TENANT_MANAGERS,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    roles: ['root', 'admin', 'manager'],
                    label: 'Managers'
                }
            },*/
            {
                path: P.TENANT_LOCATIONS,
                component: C.TENANT_LOCATIONS,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    roles: ['root', 'admin'],
                    label: 'Locations'
                }
            },
            {
                path: P.TENANT_WORKSPACES,
                component: C.TENANT_WORKSPACES,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    roles: ['root', 'admin', 'manager', 'viewer', 'tenant_admin', 'tenant_user'],
                    label: 'Workspaces'
                }
            },
            {
                path: P.USERS,
                component: C.USERS,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    roles: ['root', 'admin', 'manager', 'tenant_admin'],
                    label: 'Users'
                }
            },
            {
                path: P.ROLES,
                component: C.ROLES,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    roles: ['root', 'admin', 'manager', 'tenant_admin'],
                    label: 'Roles'
                }
            },
            // ========================================
            // RUTAS COMPARTIDAS
            // Accesibles para Admin y Normal Users
            // Requieren tenant para usuarios normales
            // ========================================
            {
                path: P.GATEWAYS,
                component: C.GATEWAYS,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['root', 'admin', 'technician', 'tenant_admin'],
                    label: 'Gateways'
                }
            },
            {
                path: P.DEVICE_PROFILES,
                component: C.DEVICE_PROFILES,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['root', 'admin', 'technician'],
                    label: 'Device Profiles'
                }
            },
            {
                path: P.APPLICATIONS,
                component: C.APPLICATIONS,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['root', 'admin', 'technician', 'tenant_admin'],
                    label: 'Applications'
                }
            },
            {
                name: 'application_devices',
                path: P.APPLICATIONS + V.APPLICATION_ID + P.DEVICES,
                component: C.DEVICES,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['root', 'admin', 'technician', 'tenant_admin'],
                    label: 'Devices'
                }
            },
            {
                name: 'device_details',
                path: P.APPLICATIONS + V.APPLICATION_ID + P.DEVICES + V.DEVICE_ID,
                component: C.DEVICE_MEASUREMENTS,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['root', 'admin', 'technician', 'tenant_admin'],
                    label: 'Device Details'
                }
            },
            {
                name: 'machine_details',
                path: P.MACHINES,
                component: C.MACHINES,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['root', 'admin', 'technician', 'tenant_admin'],
                    label: 'Machines'
                }
            },
            {
                path: P.NOTIFICATIONS,
                component: C.NOTIFICATIONS,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    label: 'Notifications'
                }
            }

        ]
    },
    {
        path: P.ROOT,
        component: C.BLANK_LAYOUT,
        children: [
            { 
                path: P.LOGIN, 
                component: C.LOGIN, 
                beforeEnter: allowAll,
                meta: { public: true, guest: true }
            },
            { 
                path: P.SIGNUP, 
                component: C.REGISTER,
                meta: { public: true, guest: true }
            },
            { 
                path: P.EMAIL_VERIFICATION, 
                component: C.EMAIL_VERIFICATION, 
                beforeEnter: allowAll,
                meta: { public: true }
            },
            {
                path: '/unauthorized',
                component: C.UNAUTHORIZED,
                beforeEnter: requireAuth,
                meta: { 
                    requiresAuth: true,
                    label: 'No Autorizado'
                }
            },
            {
                path: P.TENANT_SETUP,
                component: C.TENANT_SETUP,
                beforeEnter: requireAuth,
                meta: { 
                    requiresAuth: true,
                    label: 'Configurar Organización'
                }
            }
        ]
    }


]