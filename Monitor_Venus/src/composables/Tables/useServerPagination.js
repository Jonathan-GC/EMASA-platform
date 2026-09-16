import { ref, computed } from 'vue'

export function useServerPagination({ fetchFn, pageSize = 10 } = {}) {
  const currentPage = ref(1)
  const itemsPerPage = ref(pageSize)
  const totalCount = ref(0)

  const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / itemsPerPage.value)))
  const offset = computed(() => (currentPage.value - 1) * itemsPerPage.value)

  const setTotal = (count) => {
    totalCount.value = count ?? 0
  }

  const changePage = (page) => {
    const target = Math.min(Math.max(1, page), totalPages.value)
    if (target !== currentPage.value) {
      currentPage.value = target
      fetchFn?.()
    }
  }

  const setPageSize = (size) => {
    if (size === itemsPerPage.value) return
    itemsPerPage.value = size
    currentPage.value = 1
    fetchFn?.()
  }

  const goToNextPage = () => changePage(currentPage.value + 1)
  const goToPreviousPage = () => changePage(currentPage.value - 1)
  const resetToFirstPage = () => {
    currentPage.value = 1
  }

  return {
    currentPage,
    itemsPerPage,
    totalCount,
    totalPages,
    offset,
    changePage,
    setPageSize,
    goToNextPage,
    goToPreviousPage,
    resetToFirstPage,
    setTotal
  }
}
