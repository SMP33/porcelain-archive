import { ref, computed } from 'vue'

// Общая серверная пагинация для списковых страниц (offset/limit), без сортировки.
export function usePagedTable(fetcher, { itemsPerPage: initialItemsPerPage = 25 } = {}) {
  const page = ref(1)
  const itemsPerPage = ref(initialItemsPerPage)
  const items = ref([])
  const total = ref(0)
  const loading = ref(false)

  const pageCount = computed(() => Math.max(1, Math.ceil(total.value / itemsPerPage.value)))

  async function reload() {
    loading.value = true
    try {
      const offset = (page.value - 1) * itemsPerPage.value
      const result = await fetcher({ offset, limit: itemsPerPage.value, page: page.value, itemsPerPage: itemsPerPage.value })
      items.value = result.items
      total.value = result.total
    } finally {
      loading.value = false
    }
  }

  function goToPage(p) {
    page.value = Math.min(Math.max(1, p), pageCount.value)
    return reload()
  }

  function setItemsPerPage(n) {
    itemsPerPage.value = n
    page.value = 1
    return reload()
  }

  return { page, itemsPerPage, items, total, loading, pageCount, reload, goToPage, setItemsPerPage }
}
