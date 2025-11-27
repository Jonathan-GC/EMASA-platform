export const components = {
    DEFAULT_LAYOUT: () => import('@layouts/default.vue'),
    BLANK_LAYOUT: () => import('@layouts/blank.vue'),
    HOME: () => import('@views/home/index.vue'),
    ABOUT: () => import('@views/about/index.vue'),
    VOLTAGE: () => import('@views/voltage/index.vue'),
    CURRENT: () => import('@views/current/index.vue'),
    BATTERY: () => import('@views/battery/index.vue'),
    GATEWAYS: () => import('@views/infrastructure/gateways/index.vue'),
    DEVICE_PROFILES: () => import('@views/infrastructure/deviceProfiles/index.vue'),
    APPLICATIONS: () => import('@views/infrastructure/application/index.vue'),
    TENANTS: () => import('@views/tenants/index.vue'),
    TENANT_MANAGERS: () => import('@views/managers/index.vue'),
    TENANT_LOCATIONS: () => import('@views/locations/index.vue' ),
    TENANT_WORKSPACES: () => import('@views/workspaces/index.vue' ),
    USERS: () => import('@views/users/index.vue'),
    ROLES: () => import('@views/roles/index.vue'),
    LOGIN: () => import('@views/auth/login/index.vue'),
    REGISTER: () => import('@views/auth/signup/index.vue'),
    RESET_PASSWORD_REQUEST: () => import('@views/auth/reset-password/request.vue'),
    RESET_PASSWORD_CONFIRM: () => import('@views/auth/reset-password/confirm.vue'),
    DEVICES: () => import('@views/infrastructure/application/devices/index.vue'),
    MACHINES: () => import('@views/infrastructure/machines/index.vue'),
    DEVICE_MEASUREMENTS: () => import('@views/infrastructure/application/devices/measurments/index.vue'),
    NOTIFICATIONS: () => import('@views/notifications/index.vue'),
    EMAIL_VERIFICATION: () => import('@views/auth/verification/index.vue'),
    UNAUTHORIZED: () => import('@views/UnauthorizedView.vue'),
    TENANT_SETUP: () => import('@views/auth/tenant-setup/index.vue'),
    NOT_FOUND: () => import('@views/NotFound.vue'),

    
    // rute support
    SUPPORT: () => import('@views/support/index.vue'),
    INBOX: () => import('@views/inbox/index.vue'),
    CONVERSATION: () => import('@views/conversation/index.vue'),
    

}