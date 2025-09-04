import { paths as P } from './paths'
import { components as C } from './components'
import { requireAuth, requireGuest, allowAll } from "@utils/auth/guards.js";


export const routes = [

    { path: '/', redirect: P.LOGIN },
    {
        path: P.ROOT,
        component: C.DEFAULT_LAYOUT,
        children: [
            { path: P.HOME, component: C.HOME, beforeEnter: allowAll },
            { path: P.ABOUT, component: C.ABOUT, beforeEnter: requireAuth },
            { path: P.VOLTAGE, component: C.VOLTAGE,beforeEnter: requireAuth },
            { path: P.CURRENT, component: C.CURRENT, beforeEnter: requireAuth },
            { path: P.BATTERY, component: C.BATTERY,  beforeEnter: requireAuth},
            { path: P.GATEWAYS, component: C.GATEWAYS, beforeEnter: requireAuth },
            { path: P.DEVICE_PROFILES, component: C.DEVICE_PROFILES, beforeEnter: requireAuth },
            { path: P.APPLICATIONS, component: C.APPLICATIONS, beforeEnter: requireAuth },
            { path: P.TENANTS, component: C.TENANTS, beforeEnter: requireAuth },
            { path: P.TENANT_USERS, component: C.TENANT_USERS, beforeEnter: requireAuth },
            //{ path: P.LOGIN, component: C.LOGIN }
        ]
    },
    {
        path: P.ROOT,
        component: C.BLANK_LAYOUT,
        children: [
            { path: P.LOGIN, component: C.LOGIN, beforeEnter: allowAll },
        ]
    }


]