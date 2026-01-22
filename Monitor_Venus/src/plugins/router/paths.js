export const paths = {
    // Absolute paths
    
    ROOT: '/',
    ADMIN: '/admin',
    HOME: '/home',
    VOLTAGE: '/voltage',
    CURRENT: '/current',
    BATTERY: '/battery',
    GATEWAYS: '/infrastructure/gateways',
    DEVICE_PROFILES: '/infrastructure/device_profiles',
    APPLICATIONS: '/infrastructure/applications',
    TENANTS: '/tenants',
    TENANT_MANAGERS: '/managers',
    TENANT_LOCATIONS: '/locations',
    TENANT_WORKSPACES: '/workspaces',
    USERS: '/users',
    ROLES: '/roles',
    LOGIN: '/login',
    SIGNUP: '/signup',
    TENANT_SETUP: '/tenant-setup',
    RESET_PASSWORD_REQUEST: '/forgot-password',
    RESET_PASSWORD_CONFIRM: '/reset-password',

    // Relative paths
    DEVICES: '/devices',
    MACHINES: '/machines',
    NOTIFICATIONS: '/notifications',
    EMAIL_VERIFICATION: '/verify-email',
    DEVICE_TYPES: '/device-types',

    // Support and inbox paths
    SUPPORT: '/support',
    INBOX: '/inbox',
    CONVERSATION: '/ticket',
    NOT_FOUND: '/:pathMatch(.*)*',
}
