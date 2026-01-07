// Central Chart.js registration as a plugin for the app
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  LineController,
  BarController,
  DoughnutController,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js'
import StreamingPlugin from 'chartjs-plugin-streaming'
import ZoomPlugin from 'chartjs-plugin-zoom'

// enable date adapter globally (adapter is side-effectful and safe to import)
import 'chartjs-adapter-date-fns'

export function install(/* app */) {
  // register chart components once; idempotent on repeated calls
  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    LineController,
    BarController,
    DoughnutController,
    Title,
    Tooltip,
    Legend,
    TimeScale,
    StreamingPlugin,
    ZoomPlugin
  )
}

// default export matches registerPlugins expectation (default is a function)
export default function (app) {
  install(app)
}

// also export ChartJS in case other modules want direct access
export { ChartJS }
