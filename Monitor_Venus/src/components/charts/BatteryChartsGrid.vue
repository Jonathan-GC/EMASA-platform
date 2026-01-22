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
      :latest-data-points="latestDataPoints ? latestDataPoints[index] : []"
      :index="index"
      :device-name="deviceName"
      :y-axis-min="yAxisMin"
      :y-axis-max="yAxisMax"
      :y-left-label="yLeftLabel"
      :y-right-label="yRightLabel"
      :realtime-options="realtimeOptions"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import BatteryChart from './BatteryChart.vue'

/**
 * BatteryChartsGrid Component
 * Manages a responsive grid of BatteryChart components (dual-axis).
 * Limits the grid to a maximum of 3 columns.
 */
const props = defineProps({
  chartFragments: { type: Array, default: () => [] },
  latestDataPoints: { type: Object, default: () => ({}) },
  chartKey: { type: Number, default: 0 },
  deviceName: { type: String, default: 'Dispositivo IoT' },
  yAxisMin: { type: Number, default: null },
  yAxisMax: { type: Number, default: null },
  yLeftLabel: { type: String, default: 'Voltaje (V)' },
  yRightLabel: { type: String, default: 'Porcentaje (%)' },
  realtimeOptions: { type: Object, default: null }
})

const gridColumns = computed(() => Math.min(props.chartFragments.length, 3))
</script>

<!-- Styles moved to @/assets/css/chart-styles.css -->
