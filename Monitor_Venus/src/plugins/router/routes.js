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
                beforeEnter: allowAll,
                meta: { public: true }
            },
            {
                path: P.ABOUT,
                component: C.ABOUT,
                beforeEnter: requireAuth,
                meta: { requiresAuth: true }
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
                    roles: ['superuser', 'admin'], // Solo superuser o admin
                    label: 'Tenants'
                }
            },
            {
                path: P.TENANT_MANAGERS,
                component: C.TENANT_MANAGERS,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    roles: ['superuser', 'admin'],
                    label: 'Managers'
                }
            },
            {
                path: P.TENANT_LOCATIONS,
                component: C.TENANT_LOCATIONS,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    roles: ['superuser', 'admin'],
                    label: 'Locations'
                }
            },
            {
                path: P.TENANT_WORKSPACES,
                component: C.TENANT_WORKSPACES,
                beforeEnter: requireRoles,
                meta: { 
                    requiresAuth: true,
                    label: 'Workspaces'
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
                beforeEnter: requireTenant,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['superuser', 'admin', 'normal'],
                    label: 'Gateways'
                }
            },
            {
                path: P.DEVICE_PROFILES,
                component: C.DEVICE_PROFILES,
                beforeEnter: requireTenant,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['superuser', 'admin', 'normal'],
                    label: 'Device Profiles'
                }
            },
            {
                path: P.APPLICATIONS,
                component: C.APPLICATIONS,
                beforeEnter: requireTenant,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['superuser', 'admin', 'normal'],
                    label: 'Applications'
                }
            },
            {
                name: 'application_devices',
                path: P.APPLICATIONS + V.APPLICATION_ID + P.DEVICES,
                component: C.DEVICES,
                beforeEnter: requireTenant,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['superuser', 'admin', 'normal'],
                    label: 'Devices'
                }
            },
            {
                name: 'device_details',
                path: P.APPLICATIONS + V.APPLICATION_ID + P.DEVICES + V.DEVICE_ID,
                component: C.DEVICE_MEASUREMENTS,
                beforeEnter: requireTenant,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['superuser', 'admin', 'normal'],
                    label: 'Device Details'
                }
            },
            {
                name: 'machine_details',
                path: P.MACHINES,
                component: C.MACHINES,
                beforeEnter: requireTenant,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['superuser', 'admin', 'normal'],
                    label: 'Machines'
                }
            },
            {
                path: P.NOTIFICATIONS,
                component: C.NOTIFICATIONS,
                beforeEnter: requireTenant,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['superuser', 'admin', 'normal'],
                    label: 'Notifications'
                },
                beforeEnter: requireAuth
            },
                

         // ✅ New route Support and Inbox

            {
            path: P.SUPPORT,
            component: C.SUPPORT,    
            beforeEnter: allowAll,        
            meta: { public: true },       
            },


            {
                path: P.INBOX,
                component: C.INBOX,
                beforeEnter: requireTenant,
                meta: { 
                    requiresAuth: true,
                    requiresTenant: true,
                    roles: ['superuser', 'admin'],
                    label: 'Inbox'
                },
                beforeEnter: requireAuth
            },

            {
                path: P.CONVERSATION,
                alias: '/tickets', // Alias for email links
                component: C.CONVERSATION,
                meta: { 
                    label: 'Inbox'
                },
            },


            { path: P.TENANTS, component: C.TENANTS },
            { path: P.TENANT_MANAGERS, component: C.TENANT_MANAGERS, beforeEnter: requireAuth },
            { path: P.TENANT_LOCATIONS, component: C.TENANT_LOCATIONS, beforeEnter: requireAuth },
            { path: P.TENANT_WORKSPACES, component: C.TENANT_WORKSPACES, beforeEnter: requireAuth },
            { path: P.NOTIFICATIONS, component: C.NOTIFICATIONS, beforeEnter: requireAuth }

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