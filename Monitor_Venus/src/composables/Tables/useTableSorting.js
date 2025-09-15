import { ref } from 'vue'

export function useTableSorting() {
  // State
  const sortField = ref('')
  const sortOrder = ref({})

  // Methods
  const sortBy = (field) => {
    if (sortField.value === field) {
      // Toggle order for the same field
      sortOrder.value[field] = sortOrder.value[field] === 'asc' ? 'desc' : 'asc'
    } else {
      // Set new field and default to ascending
      sortField.value = field
      if (!sortOrder.value[field]) {
        sortOrder.value[field] = 'asc'
      }
    }
  }

  const resetSorting = () => {
    sortField.value = ''
    sortOrder.value = {}
  }

  const setSortOrder = (field, order) => {
    sortField.value = field
    sortOrder.value[field] = order
  }

  const applySorting = (items) => {
    if (!sortField.value || !items || items.length === 0) {
      return items
    }

    return [...items].sort((a, b) => {
      const field = sortField.value
      const order = sortOrder.value[field] || 'asc'
      
      let aVal = a[field]
      let bVal = b[field]

      // Handle different data types
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        aVal = aVal.toLowerCase()
        bVal = bVal.toLowerCase()
      }

      // Handle date sorting
      if (field.includes('date') || field.includes('time') || field.includes('Seen')) {
        const dateA = new Date(aVal)
        const dateB = new Date(bVal)
        
        const timeA = isNaN(dateA.getTime()) ? 0 : dateA.getTime()
        const timeB = isNaN(dateB.getTime()) ? 0 : dateB.getTime()
        
        aVal = timeA
        bVal = timeB
      }

      // Handle null/undefined values
      if (aVal == null) aVal = ''
      if (bVal == null) bVal = ''

      if (order === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }

  return {
    // State
    sortField,
    sortOrder,
    
    // Methods
    sortBy,
    resetSorting,
    setSortOrder,
    applySorting
  }
}
