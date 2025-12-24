<template>
  <div 
    class="charts-grid"
    v-if="chartFragments.length > 0"
    :style="{ '--grid-columns': gridColumns }"
  >
    <VoltageChart
      v-for="(fragment, index) in chartFragments"
      :key="`chart-${index}-${chartKey}`"
      :chart-data="fragment"
      :index="index"
      :device-name="deviceName"
      :y-axis-min="yAxisMin"
      :y-axis-max="yAxisMax"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VoltageChart from './VoltageChart.vue'

/**
 * ChartsGrid Component - Manages multiple voltage charts in a responsive grid
 * Responsibility: Layout and organize multiple charts with responsive behavior
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
  },
  yAxisMin: {
    type: Number,
    default: null
  },
  yAxisMax: {
    type: Number,
    default: null
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
