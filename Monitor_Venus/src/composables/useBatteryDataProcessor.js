import { ref } from 'vue'

/**
 * Battery data processing composable for IoT battery data
 * Handles multi-channel battery measurements with per-channel dual-axis charts
 */
export function useBatteryDataProcessor() {
    const lastDevice = ref(null)
    const recentMessages = ref([])
    const chartKey = ref(0)
    const chartDataFragments = ref([])
    const maxChannelIndex = ref(0)

    // Battery constants (from Saul's data)
    const BATTERY_MIN_V = 10.5
    const BATTERY_MAX_V = 13.2

    // Chart colors for battery channels
    const chartColors = [
        'rgb(59, 130, 246)',
        'rgba(168, 85, 247, 1)',
        'rgba(34, 197, 94, 1)',
        'rgba(251, 146, 60, 1)',
        'rgba(14, 165, 233, 1)',
        'rgba(236, 72, 153, 1)',
        'rgba(99, 102, 241, 1)'
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

    // Convert voltage to percentage
    const voltageToPercentage = (voltage) => {
        if (voltage <= BATTERY_MIN_V) return 0
        if (voltage >= BATTERY_MAX_V) return 100
        const percent = ((voltage - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V)) * 100
        return Math.round(percent)
    }

    // Extract sensor channels from different payload formats
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

    // Calculate buffer statistics from WebSocket measurements
    const calculateBufferStats = (data) => {
        const stats = {
            total_samples: 0,
            avg_value: 0,
            max_voltage: 0
        }

        if (!data.payload?.measurements?.battery) return stats

        const batteryData = data.payload.measurements.battery
        let totalSamples = 0
        let sumVoltage = 0
        let maxVoltage = -Infinity

        // Count samples and calculate battery stats from all channels
        Object.values(batteryData).forEach(channelSamples => {
            if (Array.isArray(channelSamples)) {
                channelSamples.forEach(sample => {
                    if (sample && typeof sample.value === 'number') {
                        totalSamples++
                        sumVoltage += sample.value
                        maxVoltage = Math.max(maxVoltage, sample.value)
                    }
                })
            }
        })

        stats.total_samples = totalSamples
        stats.avg_value = totalSamples > 0 ? sumVoltage / totalSamples : 0
        stats.max_voltage = maxVoltage === -Infinity ? 0 : maxVoltage

        return stats
    }

    // Computed battery percentage from max voltage
    const getBatteryPercentage = () => {
        const maxV = lastDevice.value?.buffer_stats?.max_voltage || 0
        if (maxV <= BATTERY_MIN_V) return 0
        if (maxV >= BATTERY_MAX_V) return 100
        const percent = ((maxV - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V)) * 100
        return Math.round(percent)
    }

    // Process incoming data (multi-channel battery with per-channel fragments)
    const processIncomingData = (data) => {
        if (data.error) {
            console.warn('⚠️ Datos con error recibidos:', data.error)
            return
        }

        // Extract channels for battery
        const channels = extractSensorChannels(data, 'battery')
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
        // Each fragment is a dual-axis chart (voltage + percentage)
        const fragments = []
        for (let i = 1; i <= Math.max(1, maxChannelIndex.value); i++) {
            const matchKey = incomingKeys.find(k => getChannelIndex(k) === i) || null
            const samplesRaw = matchKey ? channels[matchKey] : []
            const samples = (samplesRaw || []).map(s => ({ x: parseTime(s.time), y: s.value })).filter(p => p.x.toString() !== 'Invalid Date' && typeof p.y === 'number').sort((a, b) => a.x - b.x)
            
            // Create dual-axis datasets for this channel
            const voltageDataset = {
                label: `Voltaje ch${i} (V)`,
                data: samples,
                borderColor: chartColors[(i - 1) % chartColors.length],
                backgroundColor: chartColors[(i - 1) % chartColors.length],
                yAxisID: 'y-left',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 1,
                pointHoverRadius: 4,
                fill: false
            }

            const percentageDataset = {
                label: `Porcentaje ch${i} (%)`,
                data: samples.map(p => ({ x: p.x, y: voltageToPercentage(p.y) })),
                borderColor: 'rgb(34, 197, 94)',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                yAxisID: 'y-right',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 1,
                pointHoverRadius: 4,
                fill: false
            }

            fragments.push({ datasets: [voltageDataset, percentageDataset] })
        }

        chartDataFragments.value = fragments
        chartKey.value++

        console.log(`✅ Procesados ${fragments.length} canales de batería`)
    }

    const clearData = () => {
        chartDataFragments.value = []
        lastDevice.value = null
        recentMessages.value = []
        chartKey.value++
        maxChannelIndex.value = 0
    }

    return {
        chartDataFragments,
        lastDevice,
        recentMessages,
        chartKey,
        processIncomingData,
        clearData,
        getBatteryPercentage,
        voltageToPercentage,
        BATTERY_MIN_V,
        BATTERY_MAX_V
    }
}