<template>
  <div 
    class="charts-grid"
    v-if="chartFragments.length > 0"
    :style="{ '--grid-columns': gridColumns }"
  >
    <BatteryChart
      v-for="(fragment, index) in chartFragments"
      :key="`battery-chart-${index}-${chartKey}`"
      :chart-data="fragment"
      :index="index"
      :device-name="deviceName"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import BatteryChart from './BatteryChart.vue'

/**
 * BatteryChartsGrid Component - Manages multiple battery charts in a responsive grid
 * Each chart is dual-axis (voltage + percentage)
 * Responsibility: Layout and organize multiple dual-axis battery charts
 */
const props = defineProps({
  chartFragments: {
    type: Array,
    default: () => []
  },
  chartKey: {
    type: Number,
    default: 0
  },
  deviceName: {
    type: String,
    default: 'Dispositivo IoT'
  }
})

// Computed property for responsive grid columns
const gridColumns = computed(() => {
  const numFragments = props.chartFragments.length
  // Maximum of 3 columns per row as requested
  return Math.min(numFragments, 3)
})
</script>

<!-- Styles moved to @/assets/css/chart-styles.css -->
