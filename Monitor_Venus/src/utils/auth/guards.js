import tokenManager from './tokenManager.js';
import { useAuthStore } from '@/stores/authStore.js';
import { paths as P } from "@/plugins/router/paths"

// Helper to clear all auth data (extends tokenManager functionality)
export const clearAllAuthData = () => {
    // Use tokenManager's method for access token
    tokenManager.clearAccessToken();

    // Also clear auth cookies (not handled by tokenManager)
    document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    
    // Clear auth store
    const authStore = useAuthStore();
    authStore.logout();
};

// Route guard for protected routes (requires authentication)
export const requireAuth = (to, from, next) => {
    const authStore = useAuthStore();
    
    // Initialize auth if not already done
    if (!authStore.isAuthenticated) {
        authStore.initializeAuth();
    }
    
    if (authStore.isAuthenticated && tokenManager.hasValidToken()) {
        next();
    } else {
        console.log('🚫 Acceso denegado - No autenticado');
        clearAllAuthData();
        next(P.LOGIN);
    }
};

// Route guard for guest routes (only for non-authenticated users)
export const requireGuest = (to, from, next) => {
    if (!tokenManager.hasValidToken()) {
        next();
    } else {
        next('/dashboard');// redirect authenticated users to main area
    }
};

// Route guard for public routes (accessible to everyone)
export const allowAll = (to, from, next) => {
    next();
};

// ========================================
// ROLE-BASED GUARDS
// ========================================

/**
 * Guard para rutas que requieren ser SuperUser
 * Solo usuarios con is_superuser: true pueden acceder
 */
export const requireSuperUser = (to, from, next) => {
    const authStore = useAuthStore();
    
    // Initialize auth if needed
    if (!authStore.isAuthenticated) {
        authStore.initializeAuth();
    }
    
    if (!authStore.isAuthenticated) {
        console.log('🚫 Acceso denegado - No autenticado');
        clearAllAuthData();
        next(P.LOGIN);
        return;
    }
    
    if (authStore.isSuperUser) {
        console.log('✅ Acceso permitido - SuperUser');
        next();
    } else {
        console.log('🚫 Acceso denegado - Requiere SuperUser');
        next('/unauthorized'); // Redirigir a página de no autorizado
    }
};

/**
 * Guard para rutas que requieren ser Admin (SuperUser O Global User)
 */
export const requireAdmin = (to, from, next) => {
    const authStore = useAuthStore();
    
    if (!authStore.isAuthenticated) {
        authStore.initializeAuth();
    }
    
    if (!authStore.isAuthenticated) {
        console.log('🚫 Acceso denegado - No autenticado');
        clearAllAuthData();
        next(P.LOGIN);
        return;
    }
    
    if (authStore.isAdmin) {
        console.log('✅ Acceso permitido - Admin');
        next();
    } else {
        console.log('🚫 Acceso denegado - Requiere Admin');
        next('/unauthorized');
    }
};

/**
 * Guard para rutas de usuarios normales
 * Bloquea acceso a superusers/admins (si necesitas rutas exclusivas para users normales)
 */
export const requireNormalUser = (to, from, next) => {
    const authStore = useAuthStore();
    
    if (!authStore.isAuthenticated) {
        authStore.initializeAuth();
    }
    
    if (!authStore.isAuthenticated) {
        console.log('🚫 Acceso denegado - No autenticado');
        clearAllAuthData();
        next(P.LOGIN);
        return;
    }
    
    if (authStore.isNormalUser) {
        console.log('✅ Acceso permitido - Usuario Normal');
        next();
    } else {
        console.log('🚫 Acceso denegado - Solo usuarios normales');
        next('/dashboard'); // Redirigir admins a dashboard admin
    }
};

/**
 * Guard dinámico basado en meta.roles
 * Verifica si el usuario tiene alguno de los roles requeridos
 */
export const requireRoles = (to, from, next) => {
    const authStore = useAuthStore();
    
    if (!authStore.isAuthenticated) {
        authStore.initializeAuth();
    }
    
    if (!authStore.isAuthenticated) {
        console.log('🚫 Acceso denegado - No autenticado');
        clearAllAuthData();
        next(P.LOGIN);
        return;
    }
    
    // Obtener roles requeridos del meta de la ruta
    const requiredRoles = to.meta.roles || [];
    
    // Si no hay roles requeridos, permitir acceso
    if (requiredRoles.length === 0) {
        next();
        return;
    }
    
    // Verificar si el usuario tiene acceso
    if (authStore.canAccessRoute(requiredRoles)) {
        console.log(`✅ Acceso permitido - Roles: ${requiredRoles.join(', ')}`);
        next();
    } else {
        console.log(`🚫 Acceso denegado - Requiere roles: ${requiredRoles.join(', ')}`);
        next('/unauthorized');
    }
};

/**
 * Guard para verificar si el usuario necesita configurar un tenant
 * Si needsTenantSetup es true, redirige a /tenant-setup
 * Usar en rutas que REQUIEREN tenant (como dashboard, devices, etc.)
 */
export const requireTenant = (to, from, next) => {
    const authStore = useAuthStore();
    
    if (!authStore.isAuthenticated) {
        authStore.initializeAuth();
    }
    
    if (!authStore.isAuthenticated) {
        console.log('🚫 Acceso denegado - No autenticado');
        clearAllAuthData();
        next(P.LOGIN);
        return;
    }
    
    // Verificar si necesita configurar tenant
    if (authStore.needsTenantSetup) {
        console.log('⚠️ Usuario sin tenant - Redirigiendo a tenant-setup');
        next('/tenant-setup');
        return;
    }
    
    // Si tiene tenant o es superuser/global, permitir acceso
    console.log('✅ Usuario tiene tenant o permisos globales');
    next();
};

// ========================================
// ADDITIONAL ROLE-BASED GUARDS
// ========================================

/**
 * Guard para rutas que requieren ser Manager (tenant_admin o manager)
 */
export const requireManager = (to, from, next) => {
    const authStore = useAuthStore();
    
    if (!authStore.isAuthenticated) {
        authStore.initializeAuth();
    }
    
    if (!authStore.isAuthenticated) {
        console.log('🚫 Acceso denegado - No autenticado');
        clearAllAuthData();
        next(P.LOGIN);
        return;
    }
    
    if (authStore.isManager || authStore.isSuperUser || authStore.isGlobalUser) {
        console.log('✅ Acceso permitido - Manager o superior');
        next();
    } else {
        console.log('🚫 Acceso denegado - Requiere Manager');
        next('/unauthorized');
    }
};

/**
 * Guard para rutas que requieren ser Técnico
 */
export const requireTechnician = (to, from, next) => {
    const authStore = useAuthStore();
    
    if (!authStore.isAuthenticated) {
        authStore.initializeAuth();
    }
    
    if (!authStore.isAuthenticated) {
        console.log('🚫 Acceso denegado - No autenticado');
        clearAllAuthData();
        next(P.LOGIN);
        return;
    }
    
    if (authStore.isTechnician || authStore.isManager || authStore.isSuperUser || authStore.isGlobalUser) {
        console.log('✅ Acceso permitido - Técnico o superior');
        next();
    } else {
        console.log('🚫 Acceso denegado - Requiere Técnico');
        next('/unauthorized');
    }
};

/**
 * Guard para rutas accesibles por Viewer (solo lectura)
 */
export const requireViewer = (to, from, next) => {
    const authStore = useAuthStore();
    
    if (!authStore.isAuthenticated) {
        authStore.initializeAuth();
    }
    
    if (!authStore.isAuthenticated) {
        console.log('🚫 Acceso denegado - No autenticado');
        clearAllAuthData();
        next(P.LOGIN);
        return;
    }
    
    // Viewers tienen acceso de lectura, pero también roles superiores
    if (authStore.isViewer || authStore.isTenantUser || authStore.isTechnician || 
        authStore.isManager || authStore.isSuperUser || authStore.isGlobalUser) {
        console.log('✅ Acceso permitido - Viewer o superior');
        next();
    } else {
        console.log('🚫 Acceso denegado - Requiere al menos Viewer');
        next('/unauthorized');
    }
};

/**
 * Guard para tenant users
 */
export const requireTenantUser = (to, from, next) => {
    const authStore = useAuthStore();
    
    if (!authStore.isAuthenticated) {
        authStore.initializeAuth();
    }
    
    if (!authStore.isAuthenticated) {
        console.log('🚫 Acceso denegado - No autenticado');
        clearAllAuthData();
        next(P.LOGIN);
        return;
    }
    
    if (authStore.isTenantUser || authStore.isManager) {
        console.log('✅ Acceso permitido - Tenant User o superior');
        next();
    } else {
        console.log('🚫 Acceso denegado - Requiere Tenant User');
        next('/unauthorized');
    }
};
