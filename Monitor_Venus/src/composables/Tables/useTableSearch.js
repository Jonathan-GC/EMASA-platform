import { ref, computed } from 'vue'

export function useTableSearch(items, searchFields = []) {
  // State
  const searchText = ref('')

  // Computed
  const filteredItems = computed(() => {
    if (!items.value || !searchText.value) {
      return items.value || []
    }

    const search = searchText.value.toLowerCase()
    
    return items.value.filter(item => {
      // If no specific fields provided, search in common fields
      if (searchFields.length === 0) {
        return Object.values(item).some(value => {
          if (value == null) return false
          return String(value).toLowerCase().includes(search)
        })
      }
      
      // Search in specific fields
      return searchFields.some(field => {
        const value = getNestedValue(item, field)
        if (value == null) return false
        return String(value).toLowerCase().includes(search)
      })
    })
  })

  // Helper function to get nested object values (e.g., 'user.name')
  const getNestedValue = (obj, path) => {
    return path.split('.').reduce((current, key) => {
      return current && current[key] !== undefined ? current[key] : null
    }, obj)
  }

  // Methods
  const handleSearch = (event) => {
    searchText.value = event.target.value
  }

  const clearSearch = () => {
    searchText.value = ''
  }

  const setSearchText = (text) => {
    searchText.value = text
  }

  return {
    // State
    searchText,
    
    // Computed
    filteredItems,
    
    // Methods
    handleSearch,
    clearSearch,
    setSearchText
  }
}
