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

    // Chart data for battery measurements (multi-channel)
    const channelChartData = reactive({}); // { ch1: { data: [...] }, ch2: { data: [...] }, ... }

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

    // Process incoming data (multi-channel battery)
    const processIncomingData = (data) => {
        if (data.error) {
            console.warn('⚠️ Datos con error recibidos:', data.error)
            return
        }

        // Support new structure: measurements.battery
        const batteryMeasurements = data.measurements?.battery;
        if (!batteryMeasurements || typeof batteryMeasurements !== 'object') {
            console.log('ℹ️ Datos ignorados - esperando measurements.battery')
            return
        }

        lastDevice.value = data;
        recentMessages.value.unshift(data);
        if (recentMessages.value.length > 10) {
            recentMessages.value.pop();
        }

        // For each channel, create chart data
        Object.keys(batteryMeasurements).forEach(channel => {
            const samples = batteryMeasurements[channel];
            if (!Array.isArray(samples)) return;
            channelChartData[channel] = {
                voltage: samples.map(sample => ({ x: new Date(sample.time), y: sample.value })),
                percentage: samples.map(sample => ({ x: new Date(sample.time), y: voltageToPercentage(sample.value) }))
            };
        });
        chartKey.value++;
        console.log('✅ Gráfico de batería actualizado para canales:', Object.keys(channelChartData));
    }

    const clearData = () => {
        Object.keys(channelChartData).forEach(channel => {
            channelChartData[channel] = { voltage: [], percentage: [] };
        });
        lastDevice.value = null;
        recentMessages.value = [];
        chartKey.value++;
    }

    return {
        channelChartData,
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