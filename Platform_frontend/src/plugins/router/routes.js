import { paths as P } from './paths'
import { components as C } from './components'


export const routes = [

    { path: '/', redirect: P.HOME },
    {
        path: P.ROOT,
        component: C.DEFAULT_LAYOUT,
        children: [
            { path: P.HOME, component: C.HOME },
            { path: P.ABOUT, component: C.ABOUT },
            { path: P.VOLTAGE, component: C.VOLTAGE },
            { path: P.CURRENT, component: C.CURRENT },
            { path: P.BATTERY, component: C.BATTERY },
            { path: P.GATEWAYS, component: C.GATEWAYS },
            { path: P.DEVICE_PROFILES, component: C.DEVICE_PROFILES },
            { path: P.TENANTS, component: C.TENANTS },
            { path: P.TENANT_USERS, component: C.TENANT_USERS }

        ]
    },


]