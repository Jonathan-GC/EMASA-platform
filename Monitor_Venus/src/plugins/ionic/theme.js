// Ionic Theme Configuration
// CSS Variables for colors, spacing, and styling

export const theme = {
  // Primary color palette (Orange - based on your current request)
  primary: {
    50: '#fff7ed',
    100: '#ffedd5',
    200: '#fed7aa',
    300: '#fdba74',
    400: '#fb923c',
    500: '#f97316',
    600: '#ea580c',
    700: '#c2410c',
    800: '#9a3412',
    900: '#7c2d12',
  },
  
  // Secondary colors (Zinc)
  secondary: {
    50: '#fafafa',
    100: '#f4f4f5',
    200: '#e4e4e7',
    300: '#d4d4d8',
    400: '#a1a1aa',
    500: '#71717a',
    600: '#52525b',
    700: '#3f3f46',
    800: '#27272a',
    900: '#18181b',
  },
  
  // Success (Lime)
  success: {
    50: '#f7fee7',
    100: '#ecfccb',
    200: '#d8f999',
    300: '#bbf451',
    400: '#9ae600',
    500: '#7ccf00',
    600: '#5ea500',
    700: '#497d00',
    800: '#3c6300',
    900: '#35530e',
    DEFAULT: '#7ccf00',
    light: '#bbf451',
    dark: '#5ea500',
  },
  
  // Warning
  warning: {
    DEFAULT: '#f59e0b',
    light: '#fbbf24',
    dark: '#d97706',
  },
  
  // Error/Danger
  danger: {
    DEFAULT: '#ef4444',
    light: '#f87171',
    dark: '#dc2626',
  },
  
  // Info
  info: {
    DEFAULT: '#3b82f6',
    light: '#60a5fa',
    dark: '#2563eb',
  },
  
  // Magic (Indigo)
  magic: {
    50: '#eef2ff',
    100: '#e0e7ff',
    200: '#c7d2fe',
    300: '#a5b4fc',
    400: '#818cf8',
    500: '#6366f1',
    600: '#4f46e5',
    700: '#4338ca',
    800: '#3730a3',
    900: '#312e81',
    DEFAULT: '#6366f1',
    light: '#818cf8',
    dark: '#4338ca',
  },
  
  // Cyan (Tailwind Palette)
  cyan: {
    50: '#ecfeff',
    100: '#cffafe',
    200: '#a5f3fc',
    300: '#67e8f9',
    400: '#22d3ee',
    500: '#06b6d4',
    600: '#0891b2',
    700: '#0e7490',
    800: '#155e75',
    900: '#164e63',
    950: '#083344',
    DEFAULT: '#06b6d4',
    light: '#22d3ee',
    dark: '#0891b2',
  },
  
  // Orange (Tailwind Palette)
  orange: {
    50: '#fff7ed',
    100: '#ffedd5',
    200: '#fed7aa',
    300: '#fdba74',
    400: '#fb923c',
    500: '#f97316',
    600: '#ea580c',
    700: '#c2410c',
    800: '#9a3412',
    900: '#7c2d12',
    950: '#431407',
    DEFAULT: '#f97316',
    light: '#fb923c',
    dark: '#ea580c',
  },
  
  // Spacing scale (similar to Tailwind)
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    '2xl': '40px',
    '3xl': '48px',
  },
  
  // Border radius
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    '2xl': '24px',
    full: '9999px',
  },
  
  // Shadows
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  },
}

// Generate CSS variables for the theme
export const generateCSSVariables = () => {
  const variables = {}
  
  // Primary colors
  Object.entries(theme.primary).forEach(([key, value]) => {
    variables[`--color-primary-${key}`] = value
  })
  
  // Amber colors (alias for primary)
  Object.entries(theme.primary).forEach(([key, value]) => {
    variables[`--color-amber-${key}`] = value
  })
  
  // Secondary colors (zinc/gray)
  Object.entries(theme.secondary).forEach(([key, value]) => {
    variables[`--color-zinc-${key}`] = value
  })
  
  // Success colors (lime)
  Object.entries(theme.success).forEach(([key, value]) => {
    if (key === 'DEFAULT' || key === 'light' || key === 'dark') {
      variables[`--color-success-${key}`] = value
    } else {
      variables[`--color-lime-${key}`] = value
    }
  })
  
  // Status colors (keeping legacy variables)
  variables['--color-success'] = theme.success.DEFAULT
  variables['--color-success-light'] = theme.success.light
  variables['--color-success-dark'] = theme.success.dark
  
  variables['--color-warning'] = theme.warning.DEFAULT
  variables['--color-warning-light'] = theme.warning.light
  variables['--color-warning-dark'] = theme.warning.dark
  
  variables['--color-danger'] = theme.danger.DEFAULT
  variables['--color-danger-light'] = theme.danger.light
  variables['--color-danger-dark'] = theme.danger.dark
  
  variables['--color-info'] = theme.info.DEFAULT
  variables['--color-info-light'] = theme.info.light
  variables['--color-info-dark'] = theme.info.dark
  
  // Magic colors (indigo)
  Object.entries(theme.magic).forEach(([key, value]) => {
    if (key === 'DEFAULT' || key === 'light' || key === 'dark') {
      variables[`--color-magic-${key}`] = value
    } else {
      variables[`--color-magic-${key}`] = value
      variables[`--color-indigo-${key}`] = value
    }
  })
  
  // Cyan colors
  Object.entries(theme.cyan).forEach(([key, value]) => {
    if (key === 'DEFAULT' || key === 'light' || key === 'dark') {
      variables[`--color-cyan-${key}`] = value
    } else {
      variables[`--color-cyan-${key}`] = value
    }
  })
  
  // Orange colors
  Object.entries(theme.orange).forEach(([key, value]) => {
    if (key === 'DEFAULT' || key === 'light' || key === 'dark') {
      variables[`--color-orange-${key}`] = value
    } else {
      variables[`--color-orange-${key}`] = value
    }
  })
  
  // Spacing
  Object.entries(theme.spacing).forEach(([key, value]) => {
    variables[`--spacing-${key}`] = value
  })
  
  // Border radius
  Object.entries(theme.borderRadius).forEach(([key, value]) => {
    variables[`--radius-${key}`] = value
  })
  
  return variables
}

// Apply theme to document
export const applyTheme = () => {
  const variables = generateCSSVariables()
  const root = document.documentElement
  
  // Apply custom CSS variables
  Object.entries(variables).forEach(([key, value]) => {
    root.style.setProperty(key, value)
  })
  
  // Apply Ionic color overrides
  applyIonicColors(root)
}

// Apply Ionic color system
export const applyIonicColors = (root = document.documentElement) => {
  // Override default Ionic colors
  
  // Primary = Orange 500
  root.style.setProperty('--ion-color-primary', theme.primary[500])
  root.style.setProperty('--ion-color-primary-rgb', '249, 115, 22')
  root.style.setProperty('--ion-color-primary-contrast', '#ffffff')
  root.style.setProperty('--ion-color-primary-contrast-rgb', '255, 255, 255')
  root.style.setProperty('--ion-color-primary-shade', theme.primary[600])
  root.style.setProperty('--ion-color-primary-tint', theme.primary[400])
  
  // Secondary = Zinc 600
  root.style.setProperty('--ion-color-secondary', theme.secondary[600])
  root.style.setProperty('--ion-color-secondary-rgb', '82, 82, 91')
  root.style.setProperty('--ion-color-secondary-contrast', '#ffffff')
  root.style.setProperty('--ion-color-secondary-contrast-rgb', '255, 255, 255')
  root.style.setProperty('--ion-color-secondary-shade', theme.secondary[600])
  root.style.setProperty('--ion-color-secondary-tint', theme.secondary[400])
  
  // Success = Lime 500
  root.style.setProperty('--ion-color-success', theme.success.DEFAULT)
  root.style.setProperty('--ion-color-success-rgb', '132, 204, 22')
  root.style.setProperty('--ion-color-success-contrast', '#000000')
  root.style.setProperty('--ion-color-success-contrast-rgb', '0, 0, 0')
  root.style.setProperty('--ion-color-success-shade', theme.success.dark)
  root.style.setProperty('--ion-color-success-tint', theme.success.light)
  
  // Warning
  root.style.setProperty('--ion-color-warning', theme.warning.DEFAULT)
  root.style.setProperty('--ion-color-warning-rgb', '245, 158, 11')
  root.style.setProperty('--ion-color-warning-contrast', '#000000')
  root.style.setProperty('--ion-color-warning-contrast-rgb', '0, 0, 0')
  root.style.setProperty('--ion-color-warning-shade', theme.warning.dark)
  root.style.setProperty('--ion-color-warning-tint', theme.warning.light)
  
  // Danger
  root.style.setProperty('--ion-color-danger', theme.danger.DEFAULT)
  root.style.setProperty('--ion-color-danger-rgb', '239, 68, 68')
  root.style.setProperty('--ion-color-danger-contrast', '#ffffff')
  root.style.setProperty('--ion-color-danger-contrast-rgb', '255, 255, 255')
  root.style.setProperty('--ion-color-danger-shade', theme.danger.dark)
  root.style.setProperty('--ion-color-danger-tint', theme.danger.light)
  
  // Info
  root.style.setProperty('--ion-color-info', theme.info.DEFAULT)
  root.style.setProperty('--ion-color-info-rgb', '59, 130, 246')
  root.style.setProperty('--ion-color-info-contrast', '#ffffff')
  root.style.setProperty('--ion-color-info-contrast-rgb', '255, 255, 255')
  root.style.setProperty('--ion-color-info-shade', theme.info.dark)
  root.style.setProperty('--ion-color-info-tint', theme.info.light)
  
  // Magic = Indigo 500
  root.style.setProperty('--ion-color-magic', theme.magic[500])
  root.style.setProperty('--ion-color-magic-rgb', '99, 102, 241')
  root.style.setProperty('--ion-color-magic-contrast', '#ffffff')
  root.style.setProperty('--ion-color-magic-contrast-rgb', '255, 255, 255')
  root.style.setProperty('--ion-color-magic-shade', theme.magic[600])
  root.style.setProperty('--ion-color-magic-tint', theme.magic[400])
  
  // ✨ CUSTOM COLORS - You can use these with color="amber-500", color="zinc-700", etc.
  
  // Amber shades
  createIonicColor(root, 'amber-50', theme.primary[50])
  createIonicColor(root, 'amber-100', theme.primary[100])
  createIonicColor(root, 'amber-200', theme.primary[200])
  createIonicColor(root, 'amber-300', theme.primary[300])
  createIonicColor(root, 'amber-400', theme.primary[400])
  createIonicColor(root, 'amber-500', theme.primary[500])
  createIonicColor(root, 'amber-600', theme.primary[600])
  createIonicColor(root, 'amber-700', theme.primary[700])
  createIonicColor(root, 'amber-800', theme.primary[800])
  createIonicColor(root, 'amber-900', theme.primary[900])
  
  // Lime shades (Success)
  createIonicColor(root, 'lime-50', theme.success[50])
  createIonicColor(root, 'lime-100', theme.success[100])
  createIonicColor(root, 'lime-200', theme.success[200])
  createIonicColor(root, 'lime-300', theme.success[300])
  createIonicColor(root, 'lime-400', theme.success[400])
  createIonicColor(root, 'lime-500', theme.success[500])
  createIonicColor(root, 'lime-600', theme.success[600])
  createIonicColor(root, 'lime-700', theme.success[700])
  createIonicColor(root, 'lime-800', theme.success[800])
  createIonicColor(root, 'lime-900', theme.success[900])
  
  // Zinc shades
  createIonicColor(root, 'zinc-50', theme.secondary[50])
  createIonicColor(root, 'zinc-100', theme.secondary[100])
  createIonicColor(root, 'zinc-200', theme.secondary[200])
  createIonicColor(root, 'zinc-300', theme.secondary[300])
  createIonicColor(root, 'zinc-400', theme.secondary[400])
  createIonicColor(root, 'zinc-500', theme.secondary[500])
  createIonicColor(root, 'zinc-600', theme.secondary[600])
  createIonicColor(root, 'zinc-700', theme.secondary[700])
  createIonicColor(root, 'zinc-800', theme.secondary[800])
  createIonicColor(root, 'zinc-900', theme.secondary[900])
  
  // Magic/Indigo shades
  createIonicColor(root, 'magic-50', theme.magic[50])
  createIonicColor(root, 'magic-100', theme.magic[100])
  createIonicColor(root, 'magic-200', theme.magic[200])
  createIonicColor(root, 'magic-300', theme.magic[300])
  createIonicColor(root, 'magic-400', theme.magic[400])
  createIonicColor(root, 'magic-500', theme.magic[500])
  createIonicColor(root, 'magic-600', theme.magic[600])
  createIonicColor(root, 'magic-700', theme.magic[700])
  createIonicColor(root, 'magic-800', theme.magic[800])
  createIonicColor(root, 'magic-900', theme.magic[900])
  
  // Indigo alias (same as magic)
  createIonicColor(root, 'indigo-50', theme.magic[50])
  createIonicColor(root, 'indigo-100', theme.magic[100])
  createIonicColor(root, 'indigo-200', theme.magic[200])
  createIonicColor(root, 'indigo-300', theme.magic[300])
  createIonicColor(root, 'indigo-400', theme.magic[400])
  createIonicColor(root, 'indigo-500', theme.magic[500])
  createIonicColor(root, 'indigo-600', theme.magic[600])
  createIonicColor(root, 'indigo-700', theme.magic[700])
  createIonicColor(root, 'indigo-800', theme.magic[800])
  createIonicColor(root, 'indigo-900', theme.magic[900])
  
  // Cyan shades (Tailwind palette)
  createIonicColor(root, 'cyan-50', theme.cyan[50])
  createIonicColor(root, 'cyan-100', theme.cyan[100])
  createIonicColor(root, 'cyan-200', theme.cyan[200])
  createIonicColor(root, 'cyan-300', theme.cyan[300])
  createIonicColor(root, 'cyan-400', theme.cyan[400])
  createIonicColor(root, 'cyan-500', theme.cyan[500])
  createIonicColor(root, 'cyan-600', theme.cyan[600])
  createIonicColor(root, 'cyan-700', theme.cyan[700])
  createIonicColor(root, 'cyan-800', theme.cyan[800])
  createIonicColor(root, 'cyan-900', theme.cyan[900])
  createIonicColor(root, 'cyan-950', theme.cyan[950])
  
  // Orange shades (Tailwind palette)
  createIonicColor(root, 'orange-50', theme.orange[50])
  createIonicColor(root, 'orange-100', theme.orange[100])
  createIonicColor(root, 'orange-200', theme.orange[200])
  createIonicColor(root, 'orange-300', theme.orange[300])
  createIonicColor(root, 'orange-400', theme.orange[400])
  createIonicColor(root, 'orange-500', theme.orange[500])
  createIonicColor(root, 'orange-600', theme.orange[600])
  createIonicColor(root, 'orange-700', theme.orange[700])
  createIonicColor(root, 'orange-800', theme.orange[800])
  createIonicColor(root, 'orange-900', theme.orange[900])
  createIonicColor(root, 'orange-950', theme.orange[950])
}

// Helper function to create Ionic color variables
export const createIonicColor = (root, name, hexColor) => {
  // Convert hex to RGB
  const rgb = hexToRgb(hexColor)
  
  // Determine if color is light or dark for contrast
  const isLight = isLightColor(rgb)
  const contrastColor = isLight ? '#000000' : '#ffffff'
  const contrastRgb = isLight ? '0, 0, 0' : '255, 255, 255'
  
  // Calculate shade and tint (darker and lighter versions)
  const shade = adjustBrightness(hexColor, -10)
  const tint = adjustBrightness(hexColor, 10)
  
  // Set CSS variables
  root.style.setProperty(`--ion-color-${name}`, hexColor)
  root.style.setProperty(`--ion-color-${name}-rgb`, `${rgb.r}, ${rgb.g}, ${rgb.b}`)
  root.style.setProperty(`--ion-color-${name}-contrast`, contrastColor)
  root.style.setProperty(`--ion-color-${name}-contrast-rgb`, contrastRgb)
  root.style.setProperty(`--ion-color-${name}-shade`, shade)
  root.style.setProperty(`--ion-color-${name}-tint`, tint)
}

// Utility: Convert hex to RGB
const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : { r: 0, g: 0, b: 0 }
}

// Utility: Check if color is light
const isLightColor = (rgb) => {
  // Using relative luminance formula
  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255
  return luminance > 0.5
}

// Utility: Adjust brightness
const adjustBrightness = (hex, percent) => {
  const rgb = hexToRgb(hex)
  
  const adjust = (value) => {
    const adjusted = Math.round(value * (1 + percent / 100))
    return Math.max(0, Math.min(255, adjusted))
  }
  
  const r = adjust(rgb.r).toString(16).padStart(2, '0')
  const g = adjust(rgb.g).toString(16).padStart(2, '0')
  const b = adjust(rgb.b).toString(16).padStart(2, '0')
  
  return `#${r}${g}${b}`
}

export default theme
