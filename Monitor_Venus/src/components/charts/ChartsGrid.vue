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
      :latest-data-points="latestDataPoints ? latestDataPoints[index] : []"
      :index="index"
      :device-name="deviceName"
      :y-axis-min="yAxisMin"
      :y-axis-max="yAxisMax"
      :threshold="threshold"
      :realtime-options="realtimeOptions"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VoltageChart from './VoltageChart.vue'

/**
 * ChartsGrid Component
 * Manages a responsive grid of VoltageChart components.
 * Limits the grid to a maximum of 3 columns.
 */
const props = defineProps({
  chartFragments: { type: Array, default: () => [] },
  latestDataPoints: { type: Object, default: () => ({}) },
  chartKey: { type: Number, default: 0 },
  deviceName: { type: String, default: 'Dispositivo IoT' },
  yAxisMin: { type: Number, default: null },
  yAxisMax: { type: Number, default: null },
  threshold: { type: Number, default: null },
  realtimeOptions: { type: Object, default: null }
})

const gridColumns = computed(() => Math.min(props.chartFragments.length, 3))
</script>

<!-- Styles moved to @/assets/css/chart-styles.css -->
