import tokenManager from './tokenManager.js';
import { paths as P } from "@/plugins/router/paths"

// Helper to clear all auth data (extends tokenManager functionality)
export const clearAllAuthData = () => {
    // Use tokenManager's method for access token
    tokenManager.clearAccessToken();

    // Also clear auth cookies (not handled by tokenManager)
    document.cookie = 'refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    document.cookie = 'sessionid=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
    document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
};

// Route guard for protected routes (requires authentication)
export const requireAuth = (to, from, next) => {
    if (tokenManager.hasValidToken()) {
        next();
    } else {
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
