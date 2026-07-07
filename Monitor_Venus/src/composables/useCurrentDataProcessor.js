import { useMeasurementDataProcessor } from './useMeasurementDataProcessor'

/**
 * Current data processor - wrapper around generic measurement processor
 * Maintains backwards compatibility with existing code
 */
export function useCurrentDataProcessor() {
    const chartColors = [
        'rgb(239, 68, 68)',
        'rgba(168, 85, 247, 1)',
        'rgba(59, 130, 246, 1)',
        'rgba(34, 197, 94, 1)',
        'rgba(251, 146, 60, 1)',
        'rgba(14, 165, 233, 1)',
        'rgba(236, 72, 153, 1)'
    ]

    return useMeasurementDataProcessor({
        measurementType: 'current',
        chartColors,
        chartLabel: 'Corriente',
        unit: 'A'
    })
}