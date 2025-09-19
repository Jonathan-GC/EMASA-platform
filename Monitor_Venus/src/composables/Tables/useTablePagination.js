import { ref, computed } from 'vue'

export function useTablePagination(items, itemsPerPageDefault = 10) {
  // State
  const currentPage = ref(1)
  const itemsPerPage = ref(itemsPerPageDefault)

  // Computed
  const totalPages = computed(() => {
    if (!items.value || items.value.length === 0) return 1
    return Math.ceil(items.value.length / itemsPerPage.value)
  })

  const paginatedItems = computed(() => {
    if (!items.value) return []
    
    const start = (currentPage.value - 1) * itemsPerPage.value
    const end = start + itemsPerPage.value
    return items.value.slice(start, end)
  })

  // Methods
  const changePage = (page) => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
    }
  }

  const resetPagination = () => {
    currentPage.value = 1
  }

  const goToFirstPage = () => changePage(1)
  const goToLastPage = () => changePage(totalPages.value)
  const goToNextPage = () => changePage(currentPage.value + 1)
  const goToPreviousPage = () => changePage(currentPage.value - 1)

  return {
    // State
    currentPage,
    itemsPerPage,
    
    // Computed
    totalPages,
    paginatedItems,
    
    // Methods
    changePage,
    resetPagination,
    goToFirstPage,
    goToLastPage,
    goToNextPage,
    goToPreviousPage
  }
}
