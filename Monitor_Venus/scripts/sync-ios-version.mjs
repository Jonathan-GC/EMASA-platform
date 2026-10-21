// Sincroniza la versión del proyecto iOS con la versión canónica de package.json.
// - MARKETING_VERSION       -> package.json "version" (X.Y.Z)
// - CURRENT_PROJECT_VERSION -> major*10000 + minor*100 + patch (mismo esquema que Android)
// Se ejecuta automáticamente en build:ios / run:ios, o manualmente: pnpm run sync:versions
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')

// 1) Versión canónica desde package.json
const { version } = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'))

const parts = String(version).split('.')
if (parts.length !== 3 || !parts.every((n) => /^\d+$/.test(n))) {
  throw new Error(`package.json version "${version}" no es semver de 3 partes (X.Y.Z)`)
}
const [major, minor, patch] = parts.map((n) => parseInt(n, 10))
const buildNumber = major * 10000 + minor * 100 + patch

// 2) Parchar project.pbxproj (bloques Debug y Release)
const pbxPath = join(root, 'ios', 'App', 'App.xcodeproj', 'project.pbxproj')
let content = readFileSync(pbxPath, 'utf8')

const marketingMatches = content.match(/MARKETING_VERSION = [^;]+;/g) || []
const projectMatches = content.match(/CURRENT_PROJECT_VERSION = [^;]+;/g) || []
if (!marketingMatches.length || !projectMatches.length) {
  throw new Error(`No se encontraron MARKETING_VERSION/CURRENT_PROJECT_VERSION en ${pbxPath}`)
}

const before = content
content = content.replace(/MARKETING_VERSION = [^;]+;/g, `MARKETING_VERSION = ${version};`)
content = content.replace(/CURRENT_PROJECT_VERSION = [^;]+;/g, `CURRENT_PROJECT_VERSION = ${buildNumber};`)

if (content === before) {
  console.log(`ℹ️  Versión iOS ya sincronizada (MARKETING_VERSION=${version}, CURRENT_PROJECT_VERSION=${buildNumber})`)
} else {
  writeFileSync(pbxPath, content)
  console.log(`✅ Versión iOS sincronizada: MARKETING_VERSION=${version}, CURRENT_PROJECT_VERSION=${buildNumber} (${marketingMatches.length} bloque/s)`)
}
