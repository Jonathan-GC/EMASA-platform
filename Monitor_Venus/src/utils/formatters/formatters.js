import { format } from 'date-fns'

// Date and Time Formatters
export const formatTime = (date) => {
  if (!date) return 'N.A'
  
  try {
    let parsedDate
    
    if (date instanceof Date) {
      parsedDate = date
    } else if (typeof date === 'string' || typeof date === 'number') {
      parsedDate = new Date(date)
    } else {
      return 'Formato inválido'
    }
    
    if (isNaN(parsedDate.getTime())) {
      console.warn('Invalid date received:', date)
      return 'Fecha inválida'
    }
    
    return format(parsedDate, 'dd.MM.yyyy | HH:mm')
  } catch (error) {
    console.error('Error formatting date:', error, 'Date value:', date)
    return 'Error fecha'
  }
}

export const formatDate = (date, pattern = 'dd.MM.yyyy') => {
  if (!date) return 'N.A'
  
  try {
    const parsedDate = new Date(date)
    if (isNaN(parsedDate.getTime())) return 'Fecha inválida'
    
    return format(parsedDate, pattern)
  } catch (error) {
    console.error('Error formatting date:', error)
    return 'Error fecha'
  }
}

export const formatRelativeTime = (date) => {
  if (!date) return 'N.A'
  
  try {
    const parsedDate = new Date(date)
    if (isNaN(parsedDate.getTime())) return 'Fecha inválida'
    
    const now = new Date()
    const diffInMinutes = Math.floor((now - parsedDate) / (1000 * 60))
    
    if (diffInMinutes < 1) return 'Ahora'
    if (diffInMinutes < 60) return `Hace ${diffInMinutes} min`
    
    const diffInHours = Math.floor(diffInMinutes / 60)
    if (diffInHours < 24) return `Hace ${diffInHours} h`
    
    const diffInDays = Math.floor(diffInHours / 24)
    return `Hace ${diffInDays} días`
  } catch (error) {
    console.error('Error formatting relative time:', error)
    return 'Error fecha'
  }
}

// Status Formatters
export const getStatusColor = (status) => {
  const statusMap = {
    'online': 'success',
    'synced': 'info',
    'offline': 'danger',
    'warning': 'warning',
    'pending': 'warning',
    'active': 'success',
    'activo': 'success',
    'inactive': 'danger',
    'connected': 'success',
    'disconnected': 'danger',
    'error': 'danger',
    'success': 'success'
  }
  
  return statusMap[status?.toLowerCase()] || 'medium'
}

export const getStatusIcon = (status) => {
  const iconMap = {
    'online': 'checkmark-circle',
    'offline': 'close-circle',
    'warning': 'warning',
    'pending': 'time',
    'active': 'checkmark-circle',
    'inactive': 'close-circle',
    'connected': 'wifi',
    'disconnected': 'wifi-off',
    'error': 'alert-circle',
    'success': 'checkmark-circle'
  }
  
  return iconMap[status?.toLowerCase()] || 'help-circle'
}

export const formatStatus = (status) => {
  if (!status) return 'N.A'
  
  const statusTranslations = {
    'online': 'En línea',
    'offline': 'Desconectado',
    'warning': 'Advertencia',
    'pending': 'Pendiente',
    'active': 'Activo',
    'inactive': 'Inactivo',
    'connected': 'Conectado',
    'disconnected': 'Desconectado',
    'error': 'Error',
    'success': 'Éxito'
  }
  
  return statusTranslations[status.toLowerCase()] || status
}

// Number Formatters
export const formatCurrency = (amount, currency = 'EUR') => {
  if (amount == null) return 'N.A'
  
  try {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: currency
    }).format(amount)
  } catch (error) {
    console.error('Error formatting currency:', error)
    return `${amount} ${currency}`
  }
}

export const formatNumber = (number, decimals = 0) => {
  if (number == null) return 'N.A'
  
  try {
    return new Intl.NumberFormat('es-ES', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(number)
  } catch (error) {
    console.error('Error formatting number:', error)
    return String(number)
  }
}

export const formatFileSize = (bytes) => {
  if (bytes == null || bytes === 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const unitIndex = Math.floor(Math.log(bytes) / Math.log(1024))
  const size = bytes / Math.pow(1024, unitIndex)
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

export const formatPercentage = (value, decimals = 1) => {
  if (value == null) return 'N.A'
  
  try {
    return `${(value * 100).toFixed(decimals)}%`
  } catch (error) {
    console.error('Error formatting percentage:', error)
    return `${value}%`
  }
}

// Boolean Formatters
export const formatActiveStatus = (value) => {
  if (value === true || value === 'true' || value === 1) return 'Activo'
  if (value === false || value === 'false' || value === 0) return 'Inactivo'
  return 'N.A'
}


// String Formatters
export const formatUnderscoreToSpace = (str) => {
  if (!str) return 'N.A'
  
  try {
    return str.toString().replace(/_/g, ' ')
  } catch (error) {
    console.error('Error formatting string:', error)
    return str
  }
}
