import { ref } from 'vue'

// Minimal, safe voltage processor (alternate module to avoid Vite import issues)
export function useVoltageDataProcessor() {
  const chartDataFragments = ref([])
  const lastDevice = ref(null)
  const recentMessages = ref([])
  const chartKey = ref(0)
  // track highest numeric channel seen so we can render fixed-position cards
  const maxChannelIndex = ref(0)

  const chartColors = [
    'rgb(59, 130, 246)',
    'rgba(246, 59, 59, 1)',
    'rgba(4, 116, 0, 1)',
    'rgba(234, 179, 8, 1)',
    'rgba(99, 102, 241, 1)',
    'rgba(16, 185, 129, 1)',
    'rgba(14, 165, 233, 1)'
  ]

  const parseTime = (t) => {
    if (t === undefined || t === null) return new Date(NaN)
    if (typeof t === 'number') {
      const ms = t < 1e12 ? t * 1000 : t
      return new Date(ms)
    }
    const d = new Date(t)
    if (!isNaN(d)) return d
    const n = Number(t)
    if (!isNaN(n)) return parseTime(n)
    return new Date(NaN)
  }

  const getChannelIndex = (ch) => {
    if (!ch) return Number.MAX_SAFE_INTEGER
    const m = String(ch).toLowerCase().match(/^ch(\d+)$/i)
    if (m && m[1]) return parseInt(m[1], 10)
    const m2 = String(ch).match(/(\d+)$/)
    if (m2 && m2[1]) return parseInt(m2[1], 10)
    return Number.MAX_SAFE_INTEGER
  }

  const extractSensorChannels = (data, sensor) => {
    if (!data || typeof data !== 'object') return null
    const channels = {}
    if (Array.isArray(data.measurement_values)) {
      data.measurement_values.forEach(s => {
        if (s && s.sensor_type === sensor && typeof s.value === 'number') {
          const ch = s.channel || 'ch0'
          if (!channels[ch]) channels[ch] = []
          channels[ch].push({ time: s.time || s.time_iso || s.arrival_date, value: s.value })
        }
      })
      if (Object.keys(channels).length > 0) return channels
    }
    if (data.measurements && data.measurements[sensor]) {
      const groups = data.measurements[sensor]
      Object.entries(groups).forEach(([ch, arr]) => {
        if (!Array.isArray(arr)) return
        channels[ch] = arr.filter(s => s && typeof s.value === 'number').map(s => ({ time: s.time || s.time_iso || data.arrival_date, value: s.value }))
      })
      if (Object.keys(channels).length > 0) return channels
    }
    if (data.object && data.object.measurements && data.object.measurements[sensor]) {
      const groups = data.object.measurements[sensor]
      Object.entries(groups).forEach(([ch, arr]) => {
        if (!Array.isArray(arr)) return
        channels[ch] = arr.filter(s => s && typeof s.value === 'number').map(s => ({ time: s.time || s.time_iso || data.object.arrival_date || data.arrival_date, value: s.value }))
      })
      if (Object.keys(channels).length > 0) return channels
    }
    if (Array.isArray(data.object?.values)) {
      channels['ch0'] = data.object.values.filter(s => s && typeof s.value === 'number').map(s => ({ time: s.time || s.time_iso || data.object.arrival_date || data.arrival_date, value: s.value }))
      if (Object.keys(channels).length > 0) return channels
    }
    return null
  }

  const processIncomingData = (data) => {
    if (!data || typeof data !== 'object') return
    if (data.error) return
    const channels = extractSensorChannels(data, 'voltage')
    if (!channels) return

    // update seen device/messages
    lastDevice.value = data
    recentMessages.value.unshift(data)
    if (recentMessages.value.length > 50) recentMessages.value.pop()

    // determine numeric indices present in incoming payload and update maxChannelIndex
    const incomingKeys = Object.keys(channels)
    let highest = maxChannelIndex.value
    incomingKeys.forEach(k => {
      const idx = getChannelIndex(k)
      if (Number.isFinite(idx) && idx > 0 && idx < Number.MAX_SAFE_INTEGER && idx > highest) highest = idx
    })
    if (highest > maxChannelIndex.value) maxChannelIndex.value = highest

    // Build fragments for fixed positions: ch1..chN where N = maxChannelIndex
    const fragments = []
    for (let i = 1; i <= Math.max(1, maxChannelIndex.value); i++) {
      // find a key matching this numeric index (prefer exact ch{n})
      const matchKey = incomingKeys.find(k => getChannelIndex(k) === i) || null
      const samplesRaw = matchKey ? channels[matchKey] : []
      const samples = (samplesRaw || []).map(s => ({ x: parseTime(s.time), y: s.value })).filter(p => p.x.toString() !== 'Invalid Date' && typeof p.y === 'number').sort((a, b) => a.x - b.x)
      const color = chartColors[(i - 1) % chartColors.length]
      const dataset = { label: `Voltaje ch${i}`, data: samples, borderColor: color, backgroundColor: color, borderWidth: 2, tension: 0.1, pointRadius: 1, pointHoverRadius: 4, fill: false }
      fragments.push({ datasets: [dataset] })
    }

    chartDataFragments.value = fragments
    chartKey.value++
  }

  const clearData = () => {
    chartDataFragments.value = []
    lastDevice.value = null
    recentMessages.value = []
    chartKey.value++
    maxChannelIndex.value = 0
  }

  return { chartDataFragments, lastDevice, recentMessages, chartKey, processIncomingData, clearData }
}
