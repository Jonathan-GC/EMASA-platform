import { createRouter, createWebHistory } from 'vue-router'
import VoltageChart from '../components/VoltageChart.vue'
import CurrentChart from '../components/CurrentChart.vue'
import BatteryChart from '../components/BatteryChart.vue'

const routes = [
  {
    path: '/',
    redirect: '/voltage'
  },
  {
    path: '/voltage',
    name: 'Voltage',
    component: VoltageChart,
    meta: {
      title: 'Monitor de Voltaje'
    }
  },
  {
    path: '/current',
    name: 'Current', 
    component: CurrentChart,
    meta: {
      title: 'Monitor de Corriente'
    }
  },
  {
    path: '/battery',
    name: '/battery', 
    component: BatteryChart,
    meta: {
      title: 'Monitor de Batería'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Cambiar el título de la página según la ruta
router.beforeEach((to, from, next) => {
  document.title = to.meta?.title as string || 'IoT Monitor'
  next()
})

export default router
