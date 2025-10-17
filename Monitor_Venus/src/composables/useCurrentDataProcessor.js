import { ref, reactive } from 'vue'

/**
 * Current data processing composable for IoT current data
 * Handles data transformation and chart data creation for current measurements
 */
export function useCurrentDataProcessor() {
    const lastDevice = ref(null)
    const recentMessages = ref([])
    const chartKey = ref(0)

    // Chart data for current measurements
    const chartData = reactive({
        datasets: [{
            label: 'Corriente (A)',
            data: [],
            borderColor: 'rgb(239, 68, 68)', // Red color for current
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            borderWidth: 2,
            tension: 0.1,
            pointRadius: 1,
            pointHoverRadius: 4,
            fill: false
        }]
    })

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
     * Processes incoming WebSocket data for current measurements
     */
    const processIncomingData = (data) => {
        // Verify data doesn't have errors
        if (data.error) {
            console.warn('⚠️ Datos con error recibidos:', data.error)
            return
        }

        // Determine if payload contains current measurements
        const hasCurrent = (
            Array.isArray(data.measurement_values) && data.measurement_values.some(s => s.sensor_type === 'current')
        ) || !!(data.measurements && data.measurements.current) || !!(data.payload && data.payload.measurements && data.payload.measurements.current) || data.payload?.type === 'current'

        if (!hasCurrent) {
            console.log('ℹ️ Datos ignorados - no contienen corriente')
            return
        }

        // Update device information
        lastDevice.value = data

        // Create enhanced device object with available WebSocket data
        const enhancedDevice = {
            ...data,
            buffer_stats: calculateBufferStats(data),
            reception_timestamp: data.payload?.arrival_date || data.arrival_date || new Date().toISOString()
        }
        lastDevice.value = enhancedDevice

        // Add to recent messages with reception_timestamp and device_name
        const messageWithTimestamp = {
            ...enhancedDevice,
            reception_timestamp: enhancedDevice.reception_timestamp,
            device_name: enhancedDevice.device_name
        }
        recentMessages.value.unshift(messageWithTimestamp)
        if (recentMessages.value.length > 15) {
            recentMessages.value.pop()
        }

        // Extract current samples
        const currentSamples = extractSensorSamples(data, 'current')
        if (currentSamples && Array.isArray(currentSamples) && currentSamples.length > 0) {
            console.log(`📊 Procesando ${currentSamples.length} muestras de corriente`)

            // Convert all samples to chart points
            const newPoints = currentSamples.map(sample => ({
                x: new Date(sample.time),
                y: sample.value
            }))

            // Update chart data
            chartData.datasets[0].data = newPoints

            // Force chart update
            chartKey.value++

            console.log(`✅ Gráfico de corriente actualizado con ${newPoints.length} puntos`)
            if (newPoints.length > 0) {
                console.log(`   Tiempo: ${newPoints[0]?.x} - ${newPoints[newPoints.length - 1]?.x}`)
                console.log(`   Corriente: ${Math.min(...newPoints.map(p => p.y)).toFixed(3)}A - ${Math.max(...newPoints.map(p => p.y)).toFixed(3)}A`)
            }
        } else {
            console.log('ℹ️ No hay valores de medición de corriente en los datos recibidos')
        }
    }

    /**
     * Clears all processed data
     */
    const clearData = () => {
        chartData.datasets[0].data = []
        lastDevice.value = null
        recentMessages.value = []
        chartKey.value++
    }

    return {
        // Reactive data
        chartData,
        lastDevice,
        recentMessages,
        chartKey,

        // Methods
        processIncomingData,
        clearData
    }
}