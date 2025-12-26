import { useMeasurementDataProcessor } from './useMeasurementDataProcessor'

/**
 * Battery data processor - wrapper around generic measurement processor
 * Includes special battery percentage calculation logic
 */
export function useBatteryDataProcessor() {
    // Battery constants
    const BATTERY_MIN_V = 10.5
    const BATTERY_MAX_V = 13.2

    const chartColors = [
        'rgb(59, 130, 246)',
        'rgba(168, 85, 247, 1)',
        'rgba(34, 197, 94, 1)',
        'rgba(251, 146, 60, 1)',
        'rgba(14, 165, 233, 1)',
        'rgba(236, 72, 153, 1)',
        'rgba(99, 102, 241, 1)'
    ]

    // Convert voltage to percentage
    const voltageToPercentage = (voltage) => {
        if (voltage <= BATTERY_MIN_V) return 0
        if (voltage >= BATTERY_MAX_V) return 100
        const percent = ((voltage - BATTERY_MIN_V) / (BATTERY_MAX_V - BATTERY_MIN_V)) * 100
        return Math.round(percent)
    }

    // Special processing for battery to add max_voltage field for backwards compatibility
    const specialProcessing = (stats, data) => {
        return {
            max_voltage: stats.max_battery || 0,
            avg_value: stats.avg_battery || 0
        }
    }

    // Dataset generator for dual-axis battery charts
    const datasetGenerator = (i, samples, color) => {
        return [
            {
                label: `Voltaje ch${i} (V)`,
                data: samples,
                borderColor: color,
                backgroundColor: color,
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 1,
                fill: false,
                yAxisID: 'y-left'
            },
            {
                label: `Porcentaje ch${i} (%)`,
                data: samples.map(p => ({ x: p.x, y: voltageToPercentage(p.y) })),
                borderColor: 'rgb(34, 197, 94)',
                backgroundColor: 'rgba(34, 197, 94, 0.5)',
                borderWidth: 2,
                tension: 0.1,
                pointRadius: 1,
                fill: false,
                yAxisID: 'y-right'
            }
        ]
    }

    const processor = useMeasurementDataProcessor({
        measurementType: 'battery',
        chartColors,
        chartLabel: 'Voltaje',
        unit: 'V',
        specialProcessing,
        datasetGenerator
    })

    // Computed battery percentage from max voltage
    const getBatteryPercentage = () => {
        const maxV = processor.lastDevice.value?.buffer_stats?.max_battery || 0
        return voltageToPercentage(maxV)
    }

    return {
        ...processor,
        getBatteryPercentage,
        voltageToPercentage,
        BATTERY_MIN_V,
        BATTERY_MAX_V
    }
}