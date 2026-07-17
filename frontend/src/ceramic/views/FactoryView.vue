<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'

const props = defineProps({ id: { type: [String, Number], required: true } })
const route = useRoute()
const router = useRouter()

const PAGE_SIZE = 24

const factory = ref(null)
const documents = ref([])
const total = ref(0)
const loading = ref(true)

const page = computed(() => Math.max(1, parseInt(route.query.page) || 1))
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

async function loadFactory() {
  const { data } = await http.get(`/api/ceramic/factories/${props.id}`)
  factory.value = data
}

async function loadDocuments() {
  loading.value = true
  try {
    const { data } = await http.get(`/api/ceramic/factories/${props.id}/documents`, {
      params: { offset: (page.value - 1) * PAGE_SIZE, limit: PAGE_SIZE },
    })
    documents.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function goToPage(p) {
  router.push({ query: { ...route.query, page: p } })
}

onMounted(() => {
  loadFactory()
  loadDocuments()
})
watch(() => route.query.page, loadDocuments)
watch(() => props.id, () => {
  loadFactory()
  loadDocuments()
})
</script>

<template>
  <div v-if="factory">
    <div class="tw:border-b tw:border-gray-100">
      <div class="tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-2 tw:text-sm tw:text-gray-500 tw:flex tw:items-center tw:gap-2">
        <router-link to="/ceramic/objects" class="tw:hover:text-clay-500 tw:transition-colors">Объекты</router-link>
        <span>›</span>
        <span class="tw:text-ink-800">{{ factory.name }}</span>
      </div>
    </div>

    <main class="tw:flex-1 tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-8 tw:w-full">

      <div class="tw:mb-8 tw:pb-6 tw:border-b tw:border-clay-100">
        <h1 class="tw:font-serif tw:text-3xl tw:font-bold tw:text-ink-900 tw:mb-3">{{ factory.name }}</h1>
        <div class="tw:flex tw:flex-wrap tw:gap-4 tw:text-sm tw:text-gray-500">
          <span v-if="factory.location" class="tw:flex tw:items-center tw:gap-1">📍 {{ factory.location }}</span>
          <span v-if="factory.founded || factory.closed" class="tw:flex tw:items-center tw:gap-1">
            📅 {{ factory.founded || '?' }} — {{ factory.closed || 'н.в.' }}
          </span>
          <span class="tw:flex tw:items-center tw:gap-1">📄 {{ total }} документ(а/ов)</span>
        </div>
        <p v-if="factory.notes" class="tw:mt-3 tw:text-sm tw:text-gray-600 tw:max-w-2xl">{{ factory.notes }}</p>
      </div>

      <div v-if="documents.length" class="tw:grid tw:grid-cols-2 tw:sm:grid-cols-3 tw:md:grid-cols-4 tw:lg:grid-cols-5 tw:xl:grid-cols-6 tw:gap-4">
        <router-link v-for="doc in documents" :key="doc.id" :to="`/ceramic/document/${doc.id}`"
           class="tw:group tw:flex tw:flex-col tw:bg-white tw:rounded-lg tw:border tw:border-clay-100 tw:shadow-sm tw:hover:shadow-md tw:hover:border-clay-200 tw:transition-all tw:overflow-hidden">

          <div class="tw:bg-clay-50 tw:relative tw:overflow-hidden">
            <img v-if="doc.thumb_url" :src="doc.thumb_url" :alt="doc.title"
                 class="doc-thumb tw:w-full tw:object-cover tw:group-hover:scale-105 tw:transition-transform tw:duration-300">
            <div v-else class="doc-thumb tw:w-full tw:flex tw:items-center tw:justify-center tw:text-clay-200">
              <svg xmlns="http://www.w3.org/2000/svg" class="tw:w-12 tw:h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
            <span v-if="doc.page_count > 1" class="tw:absolute tw:bottom-1 tw:right-1 tw:bg-black/50 tw:text-white tw:text-xs tw:px-1.5 tw:py-0.5 tw:rounded">
              {{ doc.page_count }} стр.
            </span>
          </div>

          <div class="tw:p-2 tw:flex tw:flex-col tw:gap-1 tw:flex-1">
            <p class="tw:text-xs tw:font-medium tw:text-ink-800 tw:leading-snug tw:line-clamp-2 tw:group-hover:text-clay-500 tw:transition-colors">
              {{ doc.title }}
            </p>
            <div class="tw:mt-auto tw:flex tw:items-center tw:justify-between tw:gap-1">
              <span v-if="doc.doc_type" class="tw:text-xs tw:text-clay-400 tw:truncate">{{ doc.doc_type }}</span>
              <span v-if="doc.doc_date" class="tw:text-xs tw:text-gray-400 tw:shrink-0">{{ doc.doc_date }}</span>
            </div>
          </div>

        </router-link>
      </div>

      <div v-if="totalPages > 1" class="tw:mt-10 tw:flex tw:justify-center tw:items-center tw:gap-2 tw:text-sm">
        <button v-if="page > 1" @click="goToPage(page - 1)"
           class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-clay-200 tw:hover:bg-clay-50 tw:transition-colors">← Назад</button>
        <span class="tw:text-gray-500">Стр. {{ page }} из {{ totalPages }}</span>
        <button v-if="page < totalPages" @click="goToPage(page + 1)"
           class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-clay-200 tw:hover:bg-clay-50 tw:transition-colors">Вперёд →</button>
      </div>

      <div v-if="!documents.length && !loading" class="tw:text-center tw:py-20 tw:text-gray-400">
        <p>Документы ещё не добавлены</p>
      </div>

    </main>
  </div>
</template>
