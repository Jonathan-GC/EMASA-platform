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
  }
})

// Computed property for responsive grid columns
const gridColumns = computed(() => {
  const numFragments = props.chartFragments.length
  // Maximum of 3 columns per row as requested
  return Math.min(numFragments, 3)
})
</script>

<style scoped>
.charts-grid {
  display: grid;
  grid-template-columns: repeat(var(--grid-columns, 1), 1fr);
  gap: 30px;
  margin-top: 20px;
}

/* Responsive design for multiple charts */
/* Mobile: Always 1 column */
@media (max-width: 768px) {
  .charts-grid {
    grid-template-columns: 1fr !important;
    gap: 20px;
  }
}

/* Tablet: Maximum 2 columns */
@media (min-width: 769px) and (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: repeat(min(var(--grid-columns, 1), 2), 1fr) !important;
  }
}

/* Desktop: Maximum 3 columns as requested */
@media (min-width: 1025px) {
  .charts-grid {
    grid-template-columns: repeat(min(var(--grid-columns, 1), 3), 1fr);
  }
}
</style>
