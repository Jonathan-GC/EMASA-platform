export const components = {
    DEFAULT_LAYOUT: () => import('../../layouts/default.vue'),
    HOME: () => import('@views/home/index.vue'),
    ABOUT: () => import('@views/about/index.vue'),
    VOLTAGE: () => import('@views/voltage/index.vue'),
    CURRENT: () => import('@views/current/index.vue'),
    BATTERY: () => import('@views/battery/index.vue'),
    GATEWAYS: () => import('@views/infrastructure/gateways/index.vue'),
    DEVICE_PROFILES: () => import('@views/infrastructure/deviceProfiles/index.vue'),
    TENANTS: () => import('@views/tenants/index.vue'),
    TENANT_USERS: () => import('@views/users/index.vue'),
}