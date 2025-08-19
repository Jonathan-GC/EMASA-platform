import { ref } from 'vue'

/**
 * Data processing composable for IoT voltage data
 * Handles data transformation and chart data creation
 */
export function useVoltageDataProcessor() {
    const chartDataFragments = ref([])
    const lastDevice = ref(null)
    const recentMessages = ref([])
    const chartKey = ref(0)

    // Chart colors for different fragments
    const chartColors = [
        'rgb(59, 130, 246)',   // Blue
        'rgba(246, 59, 59, 1)', // Red  
        'rgba(4, 116, 0, 1)'   // Green
    ]

    /**
     * Creates chart data for a specific fragment
     */
    const createChartData = (points, fragmentIndex) => {
        const color = chartColors[fragmentIndex % chartColors.length]

        return {
            datasets: [{
                label: `Voltaje Fragmento ${fragmentIndex + 1} (V)`,
                data: points,
                borderColor: color,
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 1,
                pointHoverRadius: 4,
                fill: false
            }]
        }
    }

    /**
     * Processes incoming WebSocket data
     */
    const processIncomingData = (data) => {
        // Verify data doesn't have errors
        if (data.error) {
            console.warn('⚠️ Datos con error recibidos:', data.error)
            return
        }

        // Only process voltage data
        if (data.object?.type !== 'voltage') {
            console.log(`ℹ️ Datos ignorados - tipo: ${data.object?.type}, esperando 'voltage'`)
            return
        }

        // Update device information
        lastDevice.value = data

        // Add to recent messages
        recentMessages.value.unshift(data)
        if (recentMessages.value.length > 10) {
            recentMessages.value.pop()
        }

        // Process voltage values for charts
        const voltageValues = data.object?.values || data.measurement_values
        if (voltageValues && Array.isArray(voltageValues)) {
            console.log(`📊 Procesando ${voltageValues.length} muestras de voltaje`)

            // Convert all samples to chart points
            const allPoints = voltageValues.map(sample => ({
                x: new Date(sample.time_iso),
                y: sample.value
            }))

            // Split into fragments of 50 samples
            const fragmentSize = 50
            const fragments = []

            for (let i = 0; i < allPoints.length; i += fragmentSize) {
                const fragment = allPoints.slice(i, i + fragmentSize)
                fragments.push(fragment)
            }

            // Create chart data for each fragment
            chartDataFragments.value = fragments.map((fragment, index) =>
                createChartData(fragment, index)
            )

            // Force chart update
            chartKey.value++

            console.log(`✅ Gráficos actualizados con ${fragments.length} fragmentos`)
            fragments.forEach((fragment, index) => {
                console.log(`   Fragmento ${index + 1}: ${fragment.length} puntos`)
                if (fragment.length > 0) {
                    console.log(`     Tiempo: ${fragment[0]?.x} - ${fragment[fragment.length - 1]?.x}`)
                    console.log(`     Voltaje: ${Math.min(...fragment.map(p => p.y)).toFixed(3)}V - ${Math.max(...fragment.map(p => p.y)).toFixed(3)}V`)
                }
            })
        } else {
            console.log('ℹ️ No hay valores de medición en los datos recibidos')
        }
    }

    /**
     * Clears all processed data
     */
    const clearData = () => {
        chartDataFragments.value = []
        lastDevice.value = null
        recentMessages.value = []
        chartKey.value++
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
