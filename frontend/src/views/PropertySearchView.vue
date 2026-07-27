<template>
  <div class="tw:min-h-screen tw:bg-gray-100">
    <AppToolbar />
    <main class="tw:md:pl-[232px] tw:flex tw:flex-col tw:h-screen">
      <div class="tw:border-b tw:border-gray-200 tw:bg-white tw:px-8 tw:py-4 tw:shrink-0">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">Поиск по указателям</h1>
      </div>

      <div class="tw:flex-1 tw:min-h-0 tw:px-8 tw:py-6">
        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:h-full tw:overflow-hidden tw:flex">
          <div class="tw:w-1/4 tw:shrink-0 tw:border-r tw:border-gray-100 tw:overflow-auto">
            <div v-if="propertiesError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:m-4">
              {{ propertiesError }}
            </div>
            <div v-if="propertiesLoading" class="tw:text-sm tw:text-gray-400 tw:p-4">Загрузка…</div>
            <div v-else-if="!properties.length" class="tw:text-sm tw:text-gray-400 tw:p-4">Указателей пока нет</div>
            <ul v-else class="tw:divide-y tw:divide-gray-100">
              <li
                v-for="(item, index) in properties"
                :key="item.id"
                :title="item.description || ''"
                class="tw:px-4 tw:py-2 tw:text-sm tw:cursor-pointer tw:transition-colors"
                :class="searchSelectedProperty && searchSelectedProperty.id === item.id ? 'tw:bg-clay-50' : 'tw:hover:bg-gray-50'"
                @click="selectSearchProperty(item)"
              >
                <span class="tw:text-gray-400 tw:mr-1">{{ index + 1 }}.</span>
                <span class="tw:font-medium tw:text-gray-800" :class="{ 'tw:font-bold': item.is_system }">{{ item.title }}</span>
                <i v-if="!item.is_editable" class="mdi mdi-lock-outline tw:text-gray-400 tw:ml-1.5" title="Заблокирован от редактирования" />
                <i v-if="!item.is_usable" class="mdi mdi-key-outline tw:text-gray-400 tw:ml-1.5" title="Недоступен в документах" />
                <i v-if="!item.is_visible" class="mdi mdi-eye-off-outline tw:text-gray-400 tw:ml-1.5" title="Невидим для пользователей" />
              </li>
            </ul>
          </div>

          <div class="tw:w-2/5 tw:shrink-0 tw:border-r tw:border-gray-100 tw:flex tw:flex-col tw:min-h-0">
            <div class="tw:p-3 tw:border-b tw:border-gray-100 tw:shrink-0">
              <input
                v-model="valueFilter"
                type="search"
                placeholder="Фильтр значений…"
                :disabled="!searchSelectedProperty"
                class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300 tw:disabled:opacity-50"
                @input="loadValueCounts"
              >
            </div>
            <div class="tw:flex-1 tw:overflow-auto">
              <div v-if="!searchSelectedProperty" class="tw:text-sm tw:text-gray-400 tw:p-4">Выберите указатель слева</div>
              <div v-else-if="valueCountsError" class="tw:text-sm tw:text-red-600 tw:p-4">{{ valueCountsError }}</div>
              <div v-else-if="valueCountsLoading" class="tw:text-sm tw:text-gray-400 tw:p-4">Загрузка…</div>
              <div v-else-if="!valueCounts.length" class="tw:text-sm tw:text-gray-400 tw:p-4">Значений не найдено</div>
              <ul v-else class="tw:divide-y tw:divide-gray-100">
                <li
                  v-for="v in valueCounts"
                  :key="v.value"
                  :title="v.translated ? v.value : ''"
                  class="tw:flex tw:items-center tw:justify-between tw:gap-2 tw:px-4 tw:py-2 tw:text-sm tw:cursor-pointer tw:transition-colors"
                  :class="selectedValue === v.value ? 'tw:bg-clay-50' : 'tw:hover:bg-gray-50'"
                  @click="selectValue(v)"
                >
                  <span class="tw:text-gray-700 tw:truncate">{{ v.translated || v.value }}</span>
                  <span class="tw:text-xs tw:text-gray-400 tw:shrink-0">{{ v.count }}</span>
                </li>
              </ul>
            </div>
          </div>

          <div class="tw:flex-1 tw:overflow-auto">
            <div v-if="!selectedValue" class="tw:text-sm tw:text-gray-400 tw:p-4">Выберите значение в центре</div>
            <div v-else-if="valueDocumentsError" class="tw:text-sm tw:text-red-600 tw:p-4">{{ valueDocumentsError }}</div>
            <div v-else-if="valueDocumentsLoading" class="tw:text-sm tw:text-gray-400 tw:p-4">Загрузка…</div>
            <div v-else-if="!valueDocuments.length" class="tw:text-sm tw:text-gray-400 tw:p-4">Документов не найдено</div>
            <ul v-else class="tw:divide-y tw:divide-gray-100">
              <li v-for="doc in valueDocuments" :key="doc.id" class="tw:px-4 tw:py-2 tw:text-sm">
                <router-link :to="`/edit/document/${doc.id}`" target="_blank" class="tw:text-clay-600 tw:hover:text-clay-500 tw:transition-colors">
                  {{ doc.name }}
                </router-link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'

const router = useRouter()
const route = useRoute()
const { hasRole } = useAuth()

const properties = ref([])
const propertiesLoading = ref(true)
const propertiesError = ref('')

const searchSelectedProperty = ref(null)
const valueFilter = ref('')
const valueCounts = ref([])
const valueCountsLoading = ref(false)
const valueCountsError = ref('')
const selectedValue = ref(null)
const valueDocuments = ref([])
const valueDocumentsLoading = ref(false)
const valueDocumentsError = ref('')

async function loadProperties() {
  propertiesLoading.value = true
  propertiesError.value = ''
  try {
    const response = await http.get('/api/properties/')
    properties.value = response.data.items
  } catch (err) {
    propertiesError.value = 'Не удалось загрузить указатели.'
    console.error('Ошибка при загрузке указателей:', err)
  } finally {
    propertiesLoading.value = false
  }
}

function selectSearchProperty(item) {
  searchSelectedProperty.value = item
  valueFilter.value = ''
  selectedValue.value = null
  valueDocuments.value = []
  loadValueCounts()
}

// Выбранный указатель и текст фильтра сохраняются в query-параметрах URL,
// чтобы переживать перезагрузку страницы.
let restoringFromQuery = false

function syncQueryToUrl() {
  if (restoringFromQuery) return
  const query = { ...route.query }
  if (searchSelectedProperty.value) {
    query.property = String(searchSelectedProperty.value.id)
  } else {
    delete query.property
  }
  if (valueFilter.value) {
    query.q = valueFilter.value
  } else {
    delete query.q
  }
  router.replace({ query })
}

watch([searchSelectedProperty, valueFilter], syncQueryToUrl)

async function restoreFromQuery() {
  const propertyId = Number(route.query.property)
  const property = properties.value.find((p) => p.id === propertyId)
  if (!property) return
  restoringFromQuery = true
  try {
    searchSelectedProperty.value = property
    valueFilter.value = typeof route.query.q === 'string' ? route.query.q : ''
    await loadValueCounts()
  } finally {
    restoringFromQuery = false
  }
}

async function loadValueCounts() {
  if (!searchSelectedProperty.value) return
  valueCountsLoading.value = true
  valueCountsError.value = ''
  try {
    const { data } = await http.get(`/api/properties/${searchSelectedProperty.value.id}/value_counts`, {
      params: { q: valueFilter.value || undefined },
    })
    valueCounts.value = data.items
  } catch (err) {
    valueCountsError.value = 'Не удалось загрузить значения.'
    console.error('Ошибка при загрузке значений указателя:', err)
  } finally {
    valueCountsLoading.value = false
  }
}

async function selectValue(item) {
  selectedValue.value = item.value
  valueDocumentsLoading.value = true
  valueDocumentsError.value = ''
  try {
    const { data } = await http.get(`/api/properties/${searchSelectedProperty.value.id}/documents`, {
      params: { value: item.value },
    })
    valueDocuments.value = data.items
  } catch (err) {
    valueDocumentsError.value = 'Не удалось загрузить документы.'
    console.error('Ошибка при загрузке документов по значению указателя:', err)
  } finally {
    valueDocumentsLoading.value = false
  }
}

onMounted(async () => {
  if (!hasRole('moderator')) {
    router.push('/edit/access-denied')
    return
  }
  await loadProperties()
  await restoreFromQuery()
})
</script>
