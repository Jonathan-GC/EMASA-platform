import { ref } from 'vue'

/**
 * Generic measurement data processor for IoT measurements
 * Handles multi-channel data processing with configurable measurement types
 * @param {Object} config - Configuration object
 * @param {string} config.measurementType - Type of measurement (e.g., 'voltage', 'current', 'battery')
 * @param {Array} config.chartColors - Array of colors for chart channels
 * @param {Function} config.specialProcessing - Optional function for custom processing
 * @param {string} config.chartLabel - Label prefix for chart datasets
 * @param {string} config.unit - Unit of measurement (e.g., 'V', 'A', '%')
 */
export function useMeasurementDataProcessor(config) {
    const {
        measurementType,
        chartColors = [
            'rgb(59, 130, 246)',
            'rgba(246, 59, 59, 1)',
            'rgba(4, 116, 0, 1)',
            'rgba(234, 179, 8, 1)',
            'rgba(99, 102, 241, 1)',
            'rgba(16, 185, 129, 1)',
            'rgba(14, 165, 233, 1)'
        ],
        specialProcessing = null,
        chartLabel = null,
        unit = ''
    } = config

    const lastDevice = ref(null)
    const recentMessages = ref([])
    const chartKey = ref(0)
    const chartDataFragments = ref([])
    const maxChannelIndex = ref(0)

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
     * Extract sensor channels from different payload formats
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
                channels[ch] = arr.filter(s => s && typeof s.value === 'number').map(s => ({ 
                    time: s.time || s.time_iso || data.arrival_date, 
                    value: s.value 
                }))
            })
            if (Object.keys(channels).length > 0) return channels
        }
        
        if (data.payload && data.payload.measurements && data.payload.measurements[sensor]) {
            const groups = data.payload.measurements[sensor]
            Object.entries(groups).forEach(([ch, arr]) => {
                if (!Array.isArray(arr)) return
                channels[ch] = arr.filter(s => s && typeof s.value === 'number').map(s => ({ 
                    time: s.time || s.time_iso || data.payload.arrival_date || data.arrival_date, 
                    value: s.value 
                }))
            })
            if (Object.keys(channels).length > 0) return channels
        }
        
        if (Array.isArray(data.payload?.values)) {
            channels['ch0'] = data.payload.values.filter(s => s && typeof s.value === 'number').map(s => ({ 
                time: s.time || s.time_iso || data.payload.arrival_date || data.arrival_date, 
                value: s.value 
            }))
            if (Object.keys(channels).length > 0) return channels
        }
        
        return null
    }

    /**
     * Calculate buffer statistics from WebSocket measurements
     * Creates dynamic field names based on measurement type
     */
    const calculateBufferStats = (data) => {
        const stats = {
            total_samples: 0,
            total_fragments: 0,
            [`avg_${measurementType}`]: 0,
            [`min_${measurementType}`]: 0,
            [`max_${measurementType}`]: 0,
            [`current_${measurementType}`]: 0
        }

        const measurementData = data.payload?.measurements?.[measurementType]
        if (!measurementData) return stats

        let totalSamples = 0
        let sumValue = 0
        let minValue = Infinity
        let maxValue = -Infinity
        let latestValue = 0
        let latestTime = -Infinity

        // Calculate stats from all channels
        Object.values(measurementData).forEach(channelSamples => {
            if (Array.isArray(channelSamples)) {
                stats.total_fragments++
                channelSamples.forEach(sample => {
                    if (sample && typeof sample.value === 'number') {
                        totalSamples++
                        sumValue += sample.value
                        minValue = Math.min(minValue, sample.value)
                        maxValue = Math.max(maxValue, sample.value)
                        
                        // Track latest value by timestamp
                        const sampleTime = new Date(sample.time || sample.time_iso || 0).getTime()
                        if (sampleTime > latestTime) {
                            latestTime = sampleTime
                            latestValue = sample.value
                        }
                    }
                })
            }
        })

        stats.total_samples = totalSamples
        stats[`avg_${measurementType}`] = totalSamples > 0 ? sumValue / totalSamples : 0
        stats[`min_${measurementType}`] = minValue === Infinity ? 0 : minValue
        stats[`max_${measurementType}`] = maxValue === -Infinity ? 0 : maxValue
        stats[`current_${measurementType}`] = latestValue

        // Apply special processing if provided
        if (specialProcessing && typeof specialProcessing === 'function') {
            Object.assign(stats, specialProcessing(stats, data))
        }

        return stats
    }

    /**
     * Process incoming WebSocket data
     */
    const processIncomingData = (data) => {
        if (!data || typeof data !== 'object') return
        if (data.error) {
            console.warn('⚠️ Datos con error recibidos:', data.error)
            return
        }

        // Extract channels for this measurement type
        const channels = extractSensorChannels(data, measurementType)
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
            if (Number.isFinite(idx) && idx > 0 && idx < Number.MAX_SAFE_INTEGER && idx > highest) {
                highest = idx
            }
        })
        if (highest > maxChannelIndex.value) maxChannelIndex.value = highest

        // Build fragments for fixed positions: ch1..chN
        const fragments = []
        const label = chartLabel || measurementType.charAt(0).toUpperCase() + measurementType.slice(1)
        
        for (let i = 1; i <= Math.max(1, maxChannelIndex.value); i++) {
            const matchKey = incomingKeys.find(k => getChannelIndex(k) === i) || null
            const samplesRaw = matchKey ? channels[matchKey] : []
            const samples = (samplesRaw || [])
                .map(s => ({ x: parseTime(s.time), y: s.value }))
                .filter(p => p.x.toString() !== 'Invalid Date' && typeof p.y === 'number')
                .sort((a, b) => a.x - b.x)
            
            const color = chartColors[(i - 1) % chartColors.length]
            const dataset = {
                label: `${label} ch${i}${unit ? ' (' + unit + ')' : ''}`,
                data: samples,
                borderColor: color,
                backgroundColor: color,
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 1,
                pointHoverRadius: 4,
                fill: false
            }
            
            fragments.push({ datasets: [dataset] })
        }

        chartDataFragments.value = fragments
        chartKey.value++

        console.log(`✅ Procesados ${fragments.length} canales de ${measurementType}`)
    }

    /**
     * Clear all data
     */
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
        maxChannelIndex
    }
}
