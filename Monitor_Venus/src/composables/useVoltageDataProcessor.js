import { useMeasurementDataProcessor } from './useMeasurementDataProcessor'

/**
 * Voltage data processor - wrapper around generic measurement processor
 * Maintains backwards compatibility with existing code
 */
export function useVoltageDataProcessor() {
  const chartColors = [
    'rgb(59, 130, 246)',
    'rgba(246, 59, 59, 1)',
    'rgba(4, 116, 0, 1)',
    'rgba(234, 179, 8, 1)',
    'rgba(99, 102, 241, 1)',
    'rgba(16, 185, 129, 1)',
    'rgba(14, 165, 233, 1)'
  ]

  return useMeasurementDataProcessor({
    measurementType: 'voltage',
    chartColors,
    chartLabel: 'Voltaje',
    unit: 'V'
  })
}