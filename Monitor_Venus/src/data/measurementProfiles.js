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
  {
    value: 'energy',
    label: 'Energía',
    unit: 'kWh',
    description: 'Medición de energía consumida o generada en kilovatios-hora.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    },
  },
  {
    value: 'power',
    label: 'Potencia',
    unit: 'W',
    description: 'Medición de potencia eléctrica en vatios.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    }
  },
  {
    value: 'real_power',
    label: 'Potencia Activa',
    unit: 'W',
    description: 'Medición de la potencia real total en kilovatios.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    }
  },
  {
    value: 'reactive_power',
    label: 'Potencia Reactiva',
    unit: 'VAr',
    description: 'Medición de la potencia reactiva total en kilovoltamperios reactivos.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    }
  },
  {
    value: 'apparent_power',
    label: 'Potencia Aparente',
    unit: 'VA',
    description: 'Medición de la potencia aparente total en kilovoltamperios.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    }
  },
  {
    value: 'power_factor',
    label: 'Factor de Potencia',
    unit: '_',
    description: 'Medición del factor de potencia, sin unidad específica.',
    axes: 1,
    realtime: {
      ttl: 120000,
      duration: 30000,
      refresh: 1000,
      delay: 30000
    }
  },
  {
    value: 'frequency',
    label: 'Frecuencia',
    unit: 'Hz',
    description: 'Medición de frecuencia eléctrica en Hertz.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    }
  },
  {
    value: 'pressure',
    label: 'Presión',
    unit: 'Psi',
    description: 'Medición de presión en pascales.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    }
  },
  {
    value: 'humidity',
    label: 'Humedad',
    unit: '%',
    description: 'Medición de humedad relativa en porcentaje.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    }
  },
  {
    value: 'luminosity',
    label: 'Luminosidad',
    unit: 'lx',
    description: 'Medición de luminosidad en lux.',
    axes: 1,
    realtime: {
      ttl: 60000,
      duration: 30000,
      refresh: 1000,
      delay: 10000
    }
  }
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

// ---------------------------------------------------
// Default export – makes the module usable with `import … from …`
// ---------------------------------------------------
export default {
  MEASUREMENT_PROFILES,
  getProfileByValue,
};
