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
     * Processes incoming WebSocket data for current measurements
     */
    const processIncomingData = (data) => {
        // Verify data doesn't have errors
        if (data.error) {
            console.warn('⚠️ Datos con error recibidos:', data.error)
            return
        }

        // Only process current data
        if (data.object?.type !== 'current') {
            console.log(`ℹ️ Datos ignorados - tipo: ${data.object?.type}, esperando 'current'`)
            return
        }

        // Update device information
        lastDevice.value = data

        // Add to recent messages
        recentMessages.value.unshift(data)
        if (recentMessages.value.length > 10) {
            recentMessages.value.pop()
        }

        // Process current values for the chart
        const currentValues = data.object?.values || data.measurement_values
        if (currentValues && Array.isArray(currentValues)) {
            console.log(`📊 Procesando ${currentValues.length} muestras de corriente`)

            // Convert all samples to chart points
            const newPoints = currentValues.map(sample => ({
                x: new Date(sample.time_iso),
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
