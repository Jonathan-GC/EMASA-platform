/**
 * Helper to register plugins like Nuxt.
 * To register a plugin, export a default function that takes `app` as argument and calls `app.use`.
 * Plugins are loaded dynamically so heavy dependencies (e.g. chart.js, firebase) stay
 * out of the app entry chunk and only load when actually needed.
 */

const PLUGIN_MODULES = import.meta.glob(['./*/index.js'])

export async function registerPlugins(app) {
    const importPaths = Object.keys(PLUGIN_MODULES).sort()
    for (const path of importPaths) {
        const mod = await PLUGIN_MODULES[path]()
        if (typeof mod.default === 'function') {
            mod.default(app)
        }
    }
}
