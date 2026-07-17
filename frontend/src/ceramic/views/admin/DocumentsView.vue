<script setup>
import { ref, computed, inject, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../../api/http'

const heading = inject('adminHeading')
heading.value = 'Документы'

const route = useRoute()
const router = useRouter()
const PAGE_SIZE = 30

const factories = ref([])
const documents = ref([])
const total = ref(0)
const loading = ref(true)

const q = computed(() => route.query.q || '')
const factoryId = computed(() => parseInt(route.query.factory_id) || 0)
const issues = computed(() => route.query.issues || '')
const page = computed(() => Math.max(1, parseInt(route.query.page) || 1))
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

async function loadFactories() {
  const { data } = await http.get('/api/ceramic/factories', { params: { offset: 0, limit: 500 } })
  factories.value = data.items
}

async function loadDocuments() {
  loading.value = true
  try {
    const params = { offset: (page.value - 1) * PAGE_SIZE, limit: PAGE_SIZE }
    if (factoryId.value) params.factory_id = factoryId.value
    if (q.value) params.q = q.value
    if (issues.value) params.issues = issues.value
    const { data } = await http.get('/api/ceramic/documents', { params })
    documents.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFactories()
  loadDocuments()
})
watch(() => [route.query.q, route.query.factory_id, route.query.issues, route.query.page], loadDocuments)

function updateQuery(patch) {
  router.push({ query: { ...route.query, ...patch, page: undefined } })
}
function goToPage(p) {
  router.push({ query: { ...route.query, page: p } })
}

function rowClass(doc) {
  const noFactory = !doc.factory_name
  const noPages = !doc.page_count
  if (noFactory) return 'bg-red-50 hover:bg-red-100'
  if (noPages) return 'bg-amber-50 hover:bg-amber-100'
  return 'hover:bg-gray-50'
}
function rowTooltip(doc) {
  const noFactory = !doc.factory_name
  const noPages = !doc.page_count
  if (noFactory && noPages) return '⚠ не привязан к объекту, нет загруженных страниц'
  if (noFactory) return '⚠ не привязан к объекту'
  if (noPages) return '⚠ нет загруженных страниц'
  return ''
}

async function onDelete(doc) {
  if (!confirm(`Удалить документ «${doc.title}»?`)) return
  await http.delete(`/api/ceramic/documents/${doc.id}`)
  await loadDocuments()
}
</script>

<template>
  <div>
    <div class="tw:flex tw:flex-wrap tw:items-center tw:gap-3 tw:mb-5">
      <div class="tw:flex tw:flex-wrap tw:items-center tw:gap-2">
        <input type="text" :value="q" @change="updateQuery({ q: $event.target.value || undefined })"
               placeholder="Поиск по названию…"
               class="tw:rounded-lg tw:border tw:border-gray-200 tw:px-3 tw:py-2 tw:text-sm tw:bg-white tw:w-48 tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
        <select :value="factoryId" @change="updateQuery({ factory_id: $event.target.value || undefined })"
                class="tw:rounded-lg tw:border tw:border-gray-200 tw:px-3 tw:py-2 tw:text-sm tw:bg-white tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
          <option value="0">Все объекты</option>
          <option v-for="f in factories" :key="f.id" :value="f.id">{{ f.name }}</option>
        </select>

        <select :value="issues" @change="updateQuery({ issues: $event.target.value || undefined })"
                class="tw:rounded-lg tw:border tw:border-gray-200 tw:px-3 tw:py-2 tw:text-sm tw:bg-white tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
          <option value="">Все документы</option>
          <option value="any">⚠ Любые проблемы</option>
          <option value="no_factory">⚠ Без объекта</option>
          <option value="no_pages">⚠ Без страниц</option>
        </select>

        <span class="tw:text-sm tw:text-gray-400">{{ total }} документ(а/ов)</span>
      </div>
      <router-link to="/ceramic/admin/documents/new"
         class="tw:ml-auto tw:px-4 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:rounded-lg tw:transition-colors">
        + Добавить документ
      </router-link>
    </div>

    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
      <table class="tw:w-full tw:text-sm">
        <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
          <tr>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Название</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:sm:table-cell">Объект</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:md:table-cell">Тип</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:lg:table-cell">Дата</th>
            <th class="tw:px-4 tw:py-3 tw:text-right tw:font-medium tw:text-gray-600">Стр.</th>
            <th class="tw:px-4 tw:py-3"></th>
          </tr>
        </thead>
        <tbody class="tw:divide-y tw:divide-gray-100">
          <tr v-for="doc in documents" :key="doc.id" class="tw:transition-colors" :class="rowClass(doc)" :title="rowTooltip(doc)">
            <td class="tw:px-4 tw:py-3 tw:font-medium tw:text-gray-800 tw:max-w-xs tw:truncate">
              <span v-if="rowTooltip(doc)" class="tw:inline-flex tw:items-center tw:gap-1.5">
                <span class="tw:shrink-0 tw:text-xs" :class="!doc.factory_name ? 'tw:text-red-400' : 'tw:text-amber-400'">⚠</span>
                {{ doc.title }}
              </span>
              <template v-else>{{ doc.title }}</template>
            </td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:sm:table-cell">{{ doc.factory_name || '—' }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:md:table-cell">{{ doc.doc_type || '—' }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:lg:table-cell">{{ doc.doc_date || '—' }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-right tw:text-gray-400">{{ doc.page_count || 0 }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-right">
              <div class="tw:flex tw:items-center tw:justify-end tw:gap-2">
                <router-link :to="`/ceramic/document/${doc.id}`" target="_blank"
                   class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors tw:text-gray-500">↗</router-link>
                <router-link :to="`/ceramic/admin/documents/${doc.id}/pages`"
                   class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors tw:text-gray-500">
                  🖼 Страницы
                </router-link>
                <router-link :to="`/ceramic/admin/documents/${doc.id}/edit`"
                   class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors">
                  Изменить
                </router-link>
                <button @click="onDelete(doc)"
                        class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-red-200 tw:text-red-500 tw:hover:bg-red-50 tw:transition-colors">
                  Удалить
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!documents.length && !loading">
            <td colspan="6" class="tw:px-4 tw:py-10 tw:text-center tw:text-gray-400">Документы не найдены</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="totalPages > 1" class="tw:mt-5 tw:flex tw:justify-center tw:gap-2 tw:text-sm">
      <button v-if="page > 1" @click="goToPage(page - 1)" class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50">← Назад</button>
      <span class="tw:px-3 tw:py-1.5 tw:text-gray-500">{{ page }} / {{ totalPages }}</span>
      <button v-if="page < totalPages" @click="goToPage(page + 1)" class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50">Вперёд →</button>
    </div>
  </div>
</template>
