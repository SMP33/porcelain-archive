<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'

const route = useRoute()
const router = useRouter()

const PAGE_SIZE = 30

const docs = ref([])
const total = ref(0)
const loading = ref(true)

const page = computed(() => Math.max(1, parseInt(route.query.page) || 1))
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

// Список материалов теперь общий с porcelain_archive (таблица document) -
// у него нет фильтра/полей типа/даты, показывается только плоский список названий.
async function loadDocs() {
  loading.value = true
  try {
    const params = { offset: (page.value - 1) * PAGE_SIZE, limit: PAGE_SIZE }
    const { data } = await http.get('/api/documents/', { params })
    docs.value = data.items.map((item) => ({ id: item.id, title: item.name }))
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function goToPage(p) {
  router.push({ query: { ...route.query, page: p } })
}

onMounted(loadDocs)
watch(() => route.query.page, loadDocs)
</script>

<template>
  <div>
    <div class="tw:border-b tw:border-gray-100">
      <div class="tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-2 tw:text-sm tw:text-gray-500 tw:flex tw:items-center tw:gap-2">
        <span class="tw:text-ink-800">Материалы</span>
      </div>
    </div>

    <main class="tw:flex-1 tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-8 tw:w-full">
      <div class="tw:mb-6 tw:flex tw:flex-wrap tw:items-center tw:gap-4">
        <h1 class="tw:font-serif tw:text-3xl tw:font-bold tw:text-ink-900">Материалы</h1>
        <span class="tw:shrink-0 tw:text-sm tw:text-gray-400 tw:sm:ml-auto">{{ total }} материал(а/ов)</span>
      </div>

      <div v-if="docs.length" class="tw:space-y-2">
        <router-link v-for="doc in docs" :key="doc.id" :to="`/ceramic/document/${doc.id}`"
           class="tw:group tw:flex tw:items-center tw:gap-4 tw:bg-white tw:rounded-xl tw:border tw:border-clay-100 tw:shadow-sm tw:hover:shadow-md tw:hover:border-clay-200 tw:transition-all tw:p-3">

          <div class="tw:flex-1 tw:min-w-0">
            <p class="tw:text-sm tw:font-medium tw:text-ink-900 tw:group-hover:text-clay-500 tw:transition-colors tw:leading-snug tw:truncate">
              {{ doc.title }}
            </p>
            <div class="tw:flex tw:flex-wrap tw:items-center tw:gap-x-3 tw:gap-y-0.5 tw:mt-1">
              <span v-if="doc.doc_type" class="tw:text-xs tw:text-gray-400">{{ doc.doc_type }}</span>
              <span v-if="doc.doc_date" class="tw:text-xs tw:text-gray-400">{{ doc.doc_date }}</span>
            </div>
          </div>

          <span v-if="doc.page_count" class="tw:shrink-0 tw:text-xs tw:text-gray-400">{{ doc.page_count }} стр.</span>

        </router-link>
      </div>

      <div v-if="totalPages > 1" class="tw:mt-8 tw:flex tw:justify-center tw:items-center tw:gap-2 tw:text-sm">
        <button v-if="page > 1" @click="goToPage(page - 1)"
           class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-clay-200 tw:hover:bg-clay-50 tw:transition-colors">← Назад</button>
        <span class="tw:text-gray-500">{{ page }} / {{ totalPages }}</span>
        <button v-if="page < totalPages" @click="goToPage(page + 1)"
           class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-clay-200 tw:hover:bg-clay-50 tw:transition-colors">Вперёд →</button>
      </div>

      <div v-if="!docs.length && !loading" class="tw:text-center tw:py-20 tw:text-gray-400">
        <div class="tw:text-5xl tw:mb-4">📄</div>
        <p class="tw:text-lg">Материалы ещё не добавлены</p>
      </div>
    </main>
  </div>
</template>
