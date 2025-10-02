import { ref, reactive, computed } from 'vue'

/**
 * Battery data processing composable for IoT battery data
 */
export function useBatteryDataProcessor() {
    const lastDevice = ref(null)
    const recentMessages = ref([])
    const chartKey = ref(0)

    // Battery constants (from Saul's data)
    const BATTERY_MIN_V = 10.5
    const BATTERY_MAX_V = 13.2

    // Chart data for battery measurements (dual-axis)
    const chartData = reactive({
        datasets: [
            {
                label: 'Batería (V)',
                data: [],
                borderColor: 'rgba(4, 116, 0, 1)',
                backgroundColor: 'rgba(4, 116, 0, 0.1)',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 1,
                pointHoverRadius: 4,
                fill: false,
                yAxisID: 'y-left'
            },
            {
                label: 'Batería (%)',
                data: [],
                borderColor: 'rgba(116, 0, 87, 1)',
                backgroundColor: 'rgba(116, 0, 87, 0.1)',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 1,
                pointHoverRadius: 4,
                fill: false,
                yAxisID: 'y-right'
            }
        ]
    })

    // Computed battery percentage
    const batteryPercentage = computed(() => {
        const maxV = lastDevice.value?.buffer_stats?.max_voltage || 0
        if (maxV <= BATTERY_MIN_V) return 0
        if (maxV >= BATTERY_MAX_V) return 100
        const percent = ((maxV - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V)) * 100
        return Math.round(percent)
    })

    // Convert voltage to percentage
    const voltageToPercentage = (voltage) => {
        if (voltage <= BATTERY_MIN_V) return 0
        if (voltage >= BATTERY_MAX_V) return 100
        const percent = ((voltage - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V)) * 100
        return Math.round(percent)
    }

    // Process incoming data
    const processIncomingData = (data) => {
        if (data.error) {
            console.warn('⚠️ Datos con error recibidos:', data.error)
            return
        }

        if (data.object?.type !== 'battery') {
            console.log(`ℹ️ Datos ignorados - tipo: ${data.object?.type}, esperando 'battery'`)
            return
        }

        lastDevice.value = data

        recentMessages.value.unshift(data)
        if (recentMessages.value.length > 10) {
            recentMessages.value.pop()
        }

        const batteryValues = data.object?.values || data.measurement_values
        if (batteryValues && Array.isArray(batteryValues)) {
            console.log(`📊 Procesando ${batteryValues.length} muestras de batería`)

            const voltagePoints = batteryValues.map(sample => ({
                x: new Date(sample.time_iso),
                y: sample.value
            }))

            const percentagePoints = batteryValues.map(sample => ({
                x: new Date(sample.time_iso),
                y: voltageToPercentage(sample.value)
            }))

            chartData.datasets[0].data = voltagePoints
            chartData.datasets[1].data = percentagePoints

            chartKey.value++

            console.log(`✅ Gráfico de batería actualizado con ${voltagePoints.length} puntos`)
        }
    }

    const clearData = () => {
        chartData.datasets[0].data = []
        chartData.datasets[1].data = []
        lastDevice.value = null
        recentMessages.value = []
        chartKey.value++
    }

    return {
        chartData,
        lastDevice,
        recentMessages,
        chartKey,
        batteryPercentage,
        processIncomingData,
        clearData,
        voltageToPercentage,
        BATTERY_MIN_V,
        BATTERY_MAX_V
    }
}