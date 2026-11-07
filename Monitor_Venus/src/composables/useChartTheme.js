import { computed, watch } from 'vue'
import { Chart } from 'chart.js'
import { useTheme } from './useTheme.js'

/**
 * Chart.js palette derived from the active theme.
 *
 * Chart.js paints on a <canvas>, so CSS variables cannot reach it: the
 * colors must be real strings. Rather than editing every scale/tooltip
 * config, this module pushes the palette into Chart.defaults and repaints
 * the mounted instances whenever the theme flips.
 *
 * Importing it as a side effect (calling useChartTheme) is enough for the
 * defaults to be applied; `colors` is available for charts that need to
 * override a specific element.
 */

const PALETTE = {
  light: {
    grid: 'rgba(17, 24, 39, 0.08)',
    tick: '#6b7280',
    title: '#374151',
    tooltipBg: 'rgba(255, 255, 255, 0.96)',
    tooltipTitle: '#111827',
    tooltipBody: '#374151',
    tooltipBorder: 'rgba(17, 24, 39, 0.12)',
    pointBorder: '#ffffff',
  },
  dark: {
    grid: 'rgba(250, 250, 250, 0.12)',
    tick: '#a1a1aa',
    title: '#d4d4d8',
    tooltipBg: 'rgba(33, 33, 36, 0.96)',
    tooltipTitle: '#fafafa',
    tooltipBody: '#d4d4d8',
    tooltipBorder: 'rgba(250, 250, 250, 0.14)',
    pointBorder: '#212124',
  },
}

function applyDefaults(colors) {
  const { defaults } = Chart

  defaults.color = colors.tick
  defaults.borderColor = colors.grid

  if (defaults.plugins?.title) defaults.plugins.title.color = colors.title
  if (defaults.plugins?.legend?.labels) defaults.plugins.legend.labels.color = colors.title
  if (defaults.plugins?.tooltip) {
    defaults.plugins.tooltip.backgroundColor = colors.tooltipBg
    defaults.plugins.tooltip.titleColor = colors.tooltipTitle
    defaults.plugins.tooltip.bodyColor = colors.tooltipBody
    defaults.plugins.tooltip.borderColor = colors.tooltipBorder
    defaults.plugins.tooltip.borderWidth = 1
  }

  // Repaint everything that is already on screen.
  const instances = Chart.instances || {}
  Object.keys(instances).forEach((key) => {
    const chart = instances[key]
    if (chart && typeof chart.update === 'function') chart.update('none')
  })
}

let bound = false

export function useChartTheme() {
  const { resolved } = useTheme()

  const isDark = computed(() => resolved.value === 'dark')
  const colors = computed(() => PALETTE[resolved.value] || PALETTE.light)
  // Reactive key so individual charts can repaint if they need to.
  const version = computed(() => resolved.value)

  if (!bound) {
    bound = true
    watch(resolved, (mode) => applyDefaults(PALETTE[mode] || PALETTE.light), { immediate: true })
  }

  return { isDark, colors, version }
}

export default useChartTheme
