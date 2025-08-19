<template>
  <div class="chart-container">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  LineController,
  BarController,
  DoughnutController,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js'

// Register Chart.js components
Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  LineController,
  BarController,
  DoughnutController,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

const props = defineProps({
  type: {
    type: String,
    default: 'line'
  },
  title: {
    type: String,
    default: 'Chart'
  }
})

const chartCanvas = ref(null)
let chartInstance = null

const createChart = () => {
  const ctx = chartCanvas.value.getContext('2d')
  
  // Realistic mock data for different chart types
  const sampleData = {
    line: {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
      datasets: [
        {
          label: 'Active Users (thousands)',
          data: [45, 52, 48, 61, 55, 67, 73, 69, 78, 82, 77, 85],
          borderColor: 'rgb(54, 162, 235)',
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'New Downloads',
          data: [12, 18, 15, 22, 19, 28, 31, 26, 33, 29, 35, 42],
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          tension: 0.4,
          fill: true
        }
      ]
    },
    bar: {
      labels: ['Web Browser', 'Android App', 'iOS App', 'Desktop PWA', 'Tablet'],
      datasets: [
        {
          label: 'Daily Active Users',
          data: [2847, 4321, 3156, 892, 1567],
          backgroundColor: [
            'rgba(54, 162, 235, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(255, 206, 86, 0.8)',
            'rgba(153, 102, 255, 0.8)',
            'rgba(255, 159, 64, 0.8)'
          ],
          borderColor: [
            'rgba(54, 162, 235, 1)',
            'rgba(75, 192, 192, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(153, 102, 255, 1)',
            'rgba(255, 159, 64, 1)'
          ],
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false
        },
        {
          label: 'Monthly Growth %',
          data: [12.5, 18.3, 15.7, 8.9, 22.1],
          backgroundColor: 'rgba(255, 99, 132, 0.6)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false
        }
      ]
    },
    doughnut: {
      labels: [
        'Notifications', 
        'Charts & Analytics', 
        'Haptic Feedback', 
        'Platform Detection', 
        'Navigation', 
        'Alerts & Toasts',
        'Camera Access',
        'File Storage'
      ],
      datasets: [{
        label: 'Feature Usage %',
        data: [23.5, 18.2, 15.7, 12.3, 11.8, 9.4, 5.6, 3.5],
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
          'rgba(255, 159, 64, 0.8)',
          'rgba(199, 199, 199, 0.8)',
          'rgba(83, 102, 255, 0.8)'
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(199, 199, 199, 1)',
          'rgba(83, 102, 255, 1)'
        ],
        borderWidth: 2,
        hoverOffset: 4
      }]
    }
  }
  
  chartInstance = new Chart(ctx, {
    type: props.type,
    data: sampleData[props.type] || sampleData.line,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 1000,
        easing: 'easeInOutQuart'
      },
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        title: {
          display: true,
          text: props.title,
          font: {
            size: 18,
            weight: 'bold'
          },
          color: '#2c3e50',
          padding: 20
        },
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            padding: 20,
            usePointStyle: true,
            font: {
              size: 12
            }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: 'white',
          bodyColor: 'white',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: true,
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              if (props.type === 'doughnut') {
                label += context.parsed + '%';
              } else if (context.dataset.label?.includes('Growth')) {
                label += context.parsed + '%';
              } else if (context.dataset.label?.includes('thousands')) {
                label += (context.parsed * 1000).toLocaleString();
              } else {
                label += context.parsed.toLocaleString();
              }
              return label;
            }
          }
        }
      },
      scales: props.type !== 'doughnut' ? {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.1)',
            drawBorder: false
          },
          ticks: {
            font: {
              size: 11
            },
            color: '#666',
            callback: function(value) {
              if (this.chart.data.datasets[0].label?.includes('Growth')) {
                return value + '%';
              } else if (this.chart.data.datasets[0].label?.includes('thousands')) {
                return (value * 1000).toLocaleString();
              }
              return value.toLocaleString();
            }
          }
        },
        x: {
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
            drawBorder: false
          },
          ticks: {
            font: {
              size: 11
            },
            color: '#666'
          }
        }
      } : {}
    }
  })
}

onMounted(() => {
  createChart()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 300px;
  width: 100%;
  padding: 10px;
}
</style>
