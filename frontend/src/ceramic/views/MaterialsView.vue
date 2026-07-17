<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'

const route = useRoute()
const router = useRouter()

const PAGE_SIZE = 30

const objects = ref([])
const docs = ref([])
const total = ref(0)
const loading = ref(true)

const objectId = computed(() => parseInt(route.query.object_id) || 0)
const page = computed(() => Math.max(1, parseInt(route.query.page) || 1))
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

async function loadObjects() {
  const { data } = await http.get('/api/ceramic/factories', { params: { offset: 0, limit: 200 } })
  objects.value = data.items
}

async function loadDocs() {
  loading.value = true
  try {
    const params = { offset: (page.value - 1) * PAGE_SIZE, limit: PAGE_SIZE }
    if (objectId.value) params.factory_id = objectId.value
    const { data } = await http.get('/api/ceramic/documents', { params })
    docs.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onObjectChange(e) {
  const value = parseInt(e.target.value) || 0
  router.push({ query: { object_id: value || undefined, page: undefined } })
}
function goToPage(p) {
  router.push({ query: { ...route.query, page: p } })
}

onMounted(() => {
  loadObjects()
  loadDocs()
})
watch(() => [route.query.object_id, route.query.page], loadDocs)
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

        <div class="tw:flex tw:items-center tw:gap-2 tw:w-full tw:sm:w-auto tw:sm:ml-auto tw:min-w-0">
          <select :value="objectId" @change="onObjectChange"
                  class="tw:min-w-0 tw:flex-1 tw:sm:flex-none tw:rounded-lg tw:border tw:border-clay-100 tw:bg-white tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300">
            <option value="0">Все объекты</option>
            <option v-for="obj in objects" :key="obj.id" :value="obj.id">{{ obj.name }}</option>
          </select>
          <span class="tw:shrink-0 tw:text-sm tw:text-gray-400">{{ total }} материал(а/ов)</span>
        </div>
      </div>

      <div v-if="docs.length" class="tw:space-y-2">
        <router-link v-for="doc in docs" :key="doc.id" :to="`/ceramic/document/${doc.id}`"
           class="tw:group tw:flex tw:items-center tw:gap-4 tw:bg-white tw:rounded-xl tw:border tw:border-clay-100 tw:shadow-sm tw:hover:shadow-md tw:hover:border-clay-200 tw:transition-all tw:p-3">

          <div class="tw:flex-1 tw:min-w-0">
            <p class="tw:text-sm tw:font-medium tw:text-ink-900 tw:group-hover:text-clay-500 tw:transition-colors tw:leading-snug tw:truncate">
              {{ doc.title }}
            </p>
            <div class="tw:flex tw:flex-wrap tw:items-center tw:gap-x-3 tw:gap-y-0.5 tw:mt-1">
              <router-link v-if="doc.factory_name" :to="`/ceramic/object/${doc.factory_id}`" @click.stop
                 class="tw:text-xs tw:text-clay-400 tw:hover:text-clay-500 tw:transition-colors">
                {{ doc.factory_name }}
              </router-link>
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
