import { createRouter, createWebHistory } from '@ionic/vue-router'
import { routes } from './routes'
import tokenManager from '@/utils/auth/tokenManager'

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from) => {
    if (!from.href) {
        if (to.path === '/login' && tokenManager.hasValidToken()) {
            return '/home'
        }
    }
})

// Debug: expose available routes at runtime
/*if (typeof window !== 'undefined') {
    // log routes for debugging during dev
    console.info('Router initialized with routes:', router.getRoutes().map(r => ({ path: r.path, name: r.name })))
}*/

export default function (app) {
    app.use(router)
}

export { router }
