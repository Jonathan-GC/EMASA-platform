import { ref } from 'vue'

/**
 * Current data processing composable for IoT current data
 * Handles data transformation and chart data creation for current measurements
 * Now supports multi-channel like voltage processor
 */
export function useCurrentDataProcessor() {
    const lastDevice = ref(null)
    const recentMessages = ref([])
    const chartKey = ref(0)
    const chartDataFragments = ref([])
    const maxChannelIndex = ref(0)

    // Chart colors for current channels
    const chartColors = [
        'rgb(239, 68, 68)',
        'rgba(168, 85, 247, 1)',
        'rgba(59, 130, 246, 1)',
        'rgba(34, 197, 94, 1)',
        'rgba(251, 146, 60, 1)',
        'rgba(14, 165, 233, 1)',
        'rgba(236, 72, 153, 1)'
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

    /**
     * Helper: extract channels from different payload shapes
     */
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
        if (data.payload && data.payload.measurements && data.payload.measurements[sensor]) {
            const groups = data.payload.measurements[sensor]
            Object.entries(groups).forEach(([ch, arr]) => {
                if (!Array.isArray(arr)) return
                channels[ch] = arr.filter(s => s && typeof s.value === 'number').map(s => ({ time: s.time || s.time_iso || data.payload.arrival_date || data.arrival_date, value: s.value }))
            })
            if (Object.keys(channels).length > 0) return channels
        }
        if (Array.isArray(data.payload?.values)) {
            channels['ch0'] = data.payload.values.filter(s => s && typeof s.value === 'number').map(s => ({ time: s.time || s.time_iso || data.payload.arrival_date || data.arrival_date, value: s.value }))
            if (Object.keys(channels).length > 0) return channels
        }
        return null
    }

    /**
     * Helper: extract samples for a given sensor from different payload shapes
     */
    const extractSensorSamples = (data, sensor) => {
        if (Array.isArray(data.measurement_values)) {
            return data.measurement_values
                .filter(s => s.sensor_type === sensor && s.value !== undefined)
                .map(s => ({ time: s.time || s.time_iso || s.arrival_date || data.payload?.arrival_date, value: s.value }))
        }

        if (data.measurements && data.measurements[sensor]) {
            const channels = data.measurements[sensor]
            const samples = []
            Object.values(channels).forEach(arr => {
                if (Array.isArray(arr)) arr.forEach(s => samples.push({ time: s.time || s.time_iso || data.arrival_date, value: s.value }))
            })
            return samples
        }

        if (data.payload && data.payload.measurements && data.payload.measurements[sensor]) {
            const channels = data.payload.measurements[sensor]
            const samples = []
            Object.values(channels).forEach(arr => {
                if (Array.isArray(arr)) arr.forEach(s => samples.push({ time: s.time || s.time_iso || data.payload.arrival_date || data.arrival_date, value: s.value }))
            })
            return samples
        }

        return null
    }

    // Calculate buffer statistics from WebSocket measurements
    const calculateBufferStats = (data) => {
        const stats = {
            total_samples: 0,
            avg_voltage: 0,
            min_voltage: 0,
            max_voltage: 0
        }

        if (!data.payload?.measurements?.current) return stats

        const currentData = data.payload.measurements.current
        let totalSamples = 0
        let sumCurrent = 0
        let minCurrent = Infinity
        let maxCurrent = -Infinity

        // Count samples and calculate current stats from all channels
        Object.values(currentData).forEach(channelSamples => {
            if (Array.isArray(channelSamples)) {
                channelSamples.forEach(sample => {
                    if (sample && typeof sample.value === 'number') {
                        totalSamples++
                        sumCurrent += sample.value
                        minCurrent = Math.min(minCurrent, sample.value)
                        maxCurrent = Math.max(maxCurrent, sample.value)
                    }
                })
            }
        })

        stats.total_samples = totalSamples
        stats.avg_voltage = totalSamples > 0 ? sumCurrent / totalSamples : 0
        stats.min_voltage = minCurrent === Infinity ? 0 : minCurrent
        stats.max_voltage = maxCurrent === -Infinity ? 0 : maxCurrent

        return stats
    }

    /**
     * Processes incoming WebSocket data for current measurements (multi-channel)
     */
    const processIncomingData = (data) => {
        // Verify data doesn't have errors
        if (data.error) {
            console.warn('⚠️ Datos con error recibidos:', data.error)
            return
        }

        // Extract channels for current
        const channels = extractSensorChannels(data, 'current')
        if (!channels) return

        // Create enhanced device object
        const enhancedDevice = {
            ...data,
            buffer_stats: calculateBufferStats(data),
            reception_timestamp: data.payload?.arrival_date || data.arrival_date || new Date().toISOString()
        }
        lastDevice.value = enhancedDevice

        // Add to recent messages
        const messageWithTimestamp = {
            ...enhancedDevice,
            reception_timestamp: enhancedDevice.reception_timestamp,
            device_name: enhancedDevice.device_name
        }
        recentMessages.value.unshift(messageWithTimestamp)
        if (recentMessages.value.length > 15) recentMessages.value.pop()

        // Determine numeric indices and update maxChannelIndex
        const incomingKeys = Object.keys(channels)
        let highest = maxChannelIndex.value
        incomingKeys.forEach(k => {
            const idx = getChannelIndex(k)
            if (Number.isFinite(idx) && idx > 0 && idx < Number.MAX_SAFE_INTEGER && idx > highest) highest = idx
        })
        if (highest > maxChannelIndex.value) maxChannelIndex.value = highest

        // Build fragments for fixed positions: ch1..chN
        const fragments = []
        for (let i = 1; i <= Math.max(1, maxChannelIndex.value); i++) {
            const matchKey = incomingKeys.find(k => getChannelIndex(k) === i) || null
            const samplesRaw = matchKey ? channels[matchKey] : []
            const samples = (samplesRaw || []).map(s => ({ x: parseTime(s.time), y: s.value })).filter(p => p.x.toString() !== 'Invalid Date' && typeof p.y === 'number').sort((a, b) => a.x - b.x)
            const color = chartColors[(i - 1) % chartColors.length]
            const dataset = { label: `Corriente ch${i}`, data: samples, borderColor: color, backgroundColor: color, borderWidth: 2, tension: 0.1, pointRadius: 1, pointHoverRadius: 4, fill: false }
            fragments.push({ datasets: [dataset] })
        }

        chartDataFragments.value = fragments
        chartKey.value++

        console.log(`✅ Procesados ${fragments.length} canales de corriente`)
    }

    /**
     * Clears all processed data
     */
    const clearData = () => {
        chartDataFragments.value = []
        lastDevice.value = null
        recentMessages.value = []
        chartKey.value++
        maxChannelIndex.value = 0
    }

    return {
        // Reactive data
        chartDataFragments,
        lastDevice,
        recentMessages,
        chartKey,

        // Methods
        processIncomingData,
        clearData
    }
}