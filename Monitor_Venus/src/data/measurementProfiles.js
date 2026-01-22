/**
 * Measurement Profiles Configuration
 * Defines the approved variables EMASA-platform can offer.
 * Includes labels, units, and axis configurations.
 */

export const MEASUREMENT_PROFILES = [
  {
    value: 'voltage',
    label: 'Voltaje',
    unit: 'V',
    description: 'Medición de tensión eléctrica en Voltios.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    }
  },
  {
    value: 'current',
    label: 'Corriente',
    unit: 'A',
    description: 'Medición de intensidad eléctrica en Amperios.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    }
  },
  {
    value: 'battery',
    label: 'Batería',
    unit: 'V',
    secondaryUnit: '%',
    description: 'Nivel de carga y voltaje de batería.',
    axes: 2,
    realtime: {
      ttl: 250000,
      duration: 60000,
      refresh: 1000,
      delay: 70000
    }
  },
  /*
  {
    value: 'temperature',
    label: 'Temperatura',
    unit: '°C',
    secondaryUnit: '°F',
    description: 'Medición de temperatura ambiental o de contacto.',
    axes: 2
  },*/

];

export const getProfileByValue = (value) => {
  if (!value) return null;
  const lowerValue = value.toLowerCase();
  return MEASUREMENT_PROFILES.find(p => p.value === lowerValue) || null;
};
