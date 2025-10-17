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

    // Computed chartData for DualAxisBatteryChart component
    const chartData = computed(() => {
        // Get the first channel (assuming single channel for now)
        const channels = Object.keys(channelChartData);
        if (channels.length === 0) {
            return {
                datasets: [{
                    label: 'Voltaje (V)',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    yAxisID: 'y-left',
                    tension: 0.1,
                    pointRadius: 1,
                    pointHoverRadius: 4,
                    fill: false
                }, {
                    label: 'Porcentaje (%)',
                    data: [],
                    borderColor: 'rgb(34, 197, 94)',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    yAxisID: 'y-right',
                    tension: 0.1,
                    pointRadius: 1,
                    pointHoverRadius: 4,
                    fill: false
                }]
            };
        }

        const firstChannel = channels[0];
        const channelData = channelChartData[firstChannel];

        return {
            datasets: [{
                label: 'Voltaje (V)',
                data: channelData.voltage || [],
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                yAxisID: 'y-left',
                tension: 0.1,
                pointRadius: 1,
                pointHoverRadius: 4,
                fill: false
            }, {
                label: 'Porcentaje (%)',
                data: channelData.percentage || [],
                borderColor: 'rgb(34, 197, 94)',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                yAxisID: 'y-right',
                tension: 0.1,
                pointRadius: 1,
                pointHoverRadius: 4,
                fill: false
            }]
        };
    });

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

    // Process incoming data (multi-channel battery)
    const processIncomingData = (data) => {
        if (data.error) {
            console.warn('⚠️ Datos con error recibidos:', data.error)
            return
        }

        // Determine if payload contains battery measurements
        const hasBattery = (
            Array.isArray(data.measurement_values) && data.measurement_values.some(s => s.sensor_type === 'battery')
        ) || !!(data.measurements && data.measurements.battery) || !!(data.payload && data.payload.measurements && data.payload.measurements.battery) || data.payload?.type === 'battery'

        if (!hasBattery) {
            console.log('ℹ️ Datos ignorados - no contienen batería')
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

        // Extract battery data from various possible formats
        let batteryData = null

        // Format 1: measurements.battery
        if (data.measurements?.battery) {
            batteryData = data.measurements.battery
        }
        // Format 2: object.measurements.battery
        else if (data.payload?.measurements?.battery) {
            batteryData = data.payload.measurements.battery
        }
        // Format 3: measurement_values with sensor_type === 'battery'
        else if (Array.isArray(data.measurement_values)) {
            batteryData = {}
            data.measurement_values.forEach(s => {
                if (s && s.sensor_type === 'battery' && typeof s.value === 'number') {
                    const ch = s.channel || 'ch0'
                    if (!batteryData[ch]) batteryData[ch] = []
                    batteryData[ch].push({
                        time: s.time || s.time_iso || s.arrival_date || data.arrival_date,
                        value: s.value
                    })
                }
            })
        }

        if (!batteryData || Object.keys(batteryData).length === 0) {
            console.log('ℹ️ No se encontraron datos de batería válidos')
            return
        }

        // For each channel, create chart data
        Object.keys(batteryData).forEach(channel => {
            const samples = batteryData[channel]
            if (!Array.isArray(samples)) return
            channelChartData[channel] = {
                voltage: samples.map(sample => ({ x: new Date(sample.time), y: sample.value })),
                percentage: samples.map(sample => ({ x: new Date(sample.time), y: voltageToPercentage(sample.value) }))
            }
        })

        chartKey.value++
        console.log('✅ Gráfico de batería actualizado para canales:', Object.keys(channelChartData))
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