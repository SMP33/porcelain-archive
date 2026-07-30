<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'

const route = useRoute()
const router = useRouter()

// Документов на значение: дальше - ссылка в общий поиск, где есть пагинация.
const DOCS_LIMIT = 50

const properties = ref([])
const propertiesLoading = ref(true)
const propertiesError = ref('')

const selectedPropertyId = computed(() => Number(route.query.property) || null)
const selectedPointer = computed(() => (typeof route.query.value === 'string' ? route.query.value : ''))

const filterInput = ref(typeof route.query.q === 'string' ? route.query.q : '')

const selectedProperty = computed(
  () => properties.value.find((p) => p.id === selectedPropertyId.value) || null
)

// Фильтр по подписи значения - по тому, что реально видит пользователь (перевод).
const visibleValues = computed(() => {
  if (!selectedProperty.value) return []
  const query = filterInput.value.trim().toLowerCase()
  if (!query) return selectedProperty.value.values
  return selectedProperty.value.values.filter((v) => v.value.toLowerCase().includes(query))
})

const selectedValue = computed(
  () => (selectedProperty.value?.values || []).find((v) => v.pointer === selectedPointer.value) || null
)

const documents = ref([])
const documentsTotal = ref(0)
const documentsLoading = ref(false)
const documentsError = ref('')

async function loadProperties() {
  propertiesLoading.value = true
  propertiesError.value = ''
  try {
    const { data } = await http.get('/api/ceramic/search/facets')
    properties.value = data.properties || []
  } catch (err) {
    propertiesError.value = 'Не удалось загрузить указатели.'
    console.error('Ошибка при загрузке указателей:', err)
  } finally {
    propertiesLoading.value = false
  }
}

async function loadDocuments() {
  if (!selectedPointer.value) {
    documents.value = []
    documentsTotal.value = 0
    return
  }
  documentsLoading.value = true
  documentsError.value = ''
  try {
    const { data } = await http.get('/api/ceramic/search', {
      params: { pointer: [selectedPointer.value], offset: 0, limit: DOCS_LIMIT },
      paramsSerializer: { indexes: null },
    })
    documents.value = data.items
    documentsTotal.value = data.total
  } catch (err) {
    documentsError.value = 'Не удалось загрузить документы.'
    console.error('Ошибка при загрузке документов по значению указателя:', err)
  } finally {
    documentsLoading.value = false
  }
}

// Выбранный указатель, фильтр и значение живут в query-параметрах - состояние
// переживает перезагрузку страницы и кнопку «назад».
function selectProperty(property) {
  if (property.id === selectedPropertyId.value) return
  filterInput.value = ''
  router.push({ query: { property: String(property.id) } })
}

function selectValue(value) {
  router.push({ query: { ...route.query, value: value.pointer } })
}

watch(filterInput, (value) => {
  const current = typeof route.query.q === 'string' ? route.query.q : ''
  if (value === current) return
  router.replace({ query: { ...route.query, q: value || undefined } })
})

watch(selectedPointer, loadDocuments)

onMounted(async () => {
  await loadProperties()
  await loadDocuments()
})
</script>

<template>
  <main class="tw:flex-1 tw:max-w-6xl tw:mx-auto tw:px-4 tw:pt-16 tw:pb-16 tw:w-full" style="min-height: calc(100vh - 4rem);">

    <div class="tw:mb-6">
      <h1 class="tw:font-serif tw:text-2xl tw:font-bold tw:text-ink-900">Указатели</h1>
      <p class="tw:text-sm tw:text-gray-500 tw:mt-1">
        Выберите указатель, затем его значение - справа появятся документы, которым оно проставлено.
      </p>
    </div>

    <div v-if="propertiesError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mb-4">
      {{ propertiesError }}
    </div>

    <div v-if="propertiesLoading" class="tw:text-sm tw:text-gray-400 tw:py-16 tw:text-center">Загрузка…</div>

    <div v-else-if="!properties.length" class="tw:text-center tw:py-20 tw:text-gray-400">
      <div class="tw:text-4xl tw:mb-3">🏷</div>
      <p>Указатели ещё не проставлены документам</p>
    </div>

    <div v-else class="tw:grid tw:gap-4 tw:lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)_minmax(0,1.5fr)]">

      <!-- Указатели -->
      <section class="tw:bg-white tw:rounded-lg tw:border tw:border-clay-100 tw:shadow-sm tw:overflow-hidden tw:flex tw:flex-col">
        <p class="tw:text-xs tw:font-semibold tw:text-gray-400 tw:uppercase tw:tracking-wider tw:px-4 tw:py-3 tw:border-b tw:border-clay-100">
          Указатель
        </p>
        <ul class="tw:overflow-y-auto tw:lg:max-h-[60vh]">
          <li v-for="prop in properties" :key="prop.id">
            <button type="button" @click="selectProperty(prop)"
                    class="tw:w-full tw:text-left tw:flex tw:items-center tw:justify-between tw:gap-2 tw:px-4 tw:py-2.5 tw:text-sm tw:transition-colors"
                    :class="selectedPropertyId === prop.id ? 'tw:bg-clay-100 tw:text-clay-700 tw:font-medium' : 'tw:text-gray-600 tw:hover:bg-gray-100'">
              <span class="tw:truncate">{{ prop.title }}</span>
              <span class="tw:text-xs tw:text-gray-400 tw:shrink-0">{{ prop.values.length }}</span>
            </button>
          </li>
        </ul>
      </section>

      <!-- Значения -->
      <section class="tw:bg-white tw:rounded-lg tw:border tw:border-clay-100 tw:shadow-sm tw:overflow-hidden tw:flex tw:flex-col">
        <div class="tw:px-3 tw:py-2.5 tw:border-b tw:border-clay-100">
          <input v-model="filterInput" type="search" placeholder="Фильтр значений…" :disabled="!selectedProperty"
                 class="tw:w-full tw:rounded-lg tw:border tw:border-clay-200 tw:px-3 tw:py-1.5 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300 tw:disabled:opacity-50 tw:bg-white">
        </div>
        <div v-if="!selectedProperty" class="tw:text-sm tw:text-gray-400 tw:px-4 tw:py-4">Выберите указатель слева</div>
        <div v-else-if="!visibleValues.length" class="tw:text-sm tw:text-gray-400 tw:px-4 tw:py-4">Значений не найдено</div>
        <ul v-else class="tw:overflow-y-auto tw:lg:max-h-[calc(60vh-3.25rem)]">
          <li v-for="v in visibleValues" :key="v.pointer">
            <button type="button" @click="selectValue(v)"
                    class="tw:w-full tw:text-left tw:flex tw:items-center tw:justify-between tw:gap-2 tw:px-4 tw:py-2 tw:text-sm tw:transition-colors"
                    :class="selectedPointer === v.pointer ? 'tw:bg-clay-100 tw:text-clay-700 tw:font-medium' : 'tw:text-gray-600 tw:hover:bg-gray-100'">
              <span class="tw:truncate">{{ v.value }}</span>
              <span class="tw:text-xs tw:text-gray-400 tw:shrink-0">{{ v.count }}</span>
            </button>
          </li>
        </ul>
      </section>

      <!-- Документы -->
      <section class="tw:bg-white tw:rounded-lg tw:border tw:border-clay-100 tw:shadow-sm tw:overflow-hidden tw:flex tw:flex-col">
        <div class="tw:flex tw:items-center tw:justify-between tw:gap-2 tw:px-4 tw:py-3 tw:border-b tw:border-clay-100">
          <p class="tw:text-xs tw:font-semibold tw:text-gray-400 tw:uppercase tw:tracking-wider tw:truncate">
            {{ selectedValue ? selectedValue.value : 'Документы' }}
          </p>
          <router-link v-if="selectedPointer" :to="{ path: '/materials', query: { pointer: selectedPointer } }"
                       class="tw:text-xs tw:text-clay-600 tw:hover:text-clay-500 tw:transition-colors tw:shrink-0">
            В поиске →
          </router-link>
        </div>

        <div v-if="!selectedPointer" class="tw:text-sm tw:text-gray-400 tw:px-4 tw:py-4">Выберите значение</div>
        <div v-else-if="documentsError" class="tw:text-sm tw:text-red-600 tw:px-4 tw:py-4">{{ documentsError }}</div>
        <div v-else-if="documentsLoading" class="tw:text-sm tw:text-gray-400 tw:px-4 tw:py-4">Загрузка…</div>
        <div v-else-if="!documents.length" class="tw:text-sm tw:text-gray-400 tw:px-4 tw:py-4">Документов не найдено</div>
        <template v-else>
          <ul class="tw:overflow-y-auto tw:divide-y tw:divide-clay-50 tw:lg:max-h-[calc(60vh-3.25rem)]">
            <li v-for="doc in documents" :key="doc.id">
              <router-link :to="`/document/${doc.id}`"
                           class="tw:group tw:flex tw:items-center tw:gap-3 tw:px-4 tw:py-2.5 tw:hover:bg-gray-50 tw:transition-colors">
                <div class="tw:w-10 tw:h-10 tw:shrink-0 tw:rounded tw:overflow-hidden tw:bg-gray-100">
                  <img v-if="doc.thumb_url" :src="doc.thumb_url" alt="" loading="lazy" class="tw:w-full tw:h-full tw:object-cover tw:object-top">
                  <div v-else class="stripe-placeholder tw:w-full tw:h-full"></div>
                </div>
                <div class="tw:min-w-0 tw:flex-1">
                  <p class="tw:text-sm tw:text-ink-900 tw:group-hover:text-clay-500 tw:transition-colors tw:truncate">{{ doc.title }}</p>
                  <p v-if="doc.page_count" class="tw:text-xs tw:text-gray-400">{{ doc.page_count }} стр.</p>
                </div>
              </router-link>
            </li>
          </ul>
          <p v-if="documentsTotal > documents.length" class="tw:text-xs tw:text-gray-400 tw:px-4 tw:py-2.5 tw:border-t tw:border-clay-100">
            Показаны первые {{ documents.length }} из {{ documentsTotal }} -
            <router-link :to="{ path: '/materials', query: { pointer: selectedPointer } }" class="tw:text-clay-600 tw:hover:text-clay-500">
              смотреть все в поиске
            </router-link>
          </p>
        </template>
      </section>

    </div>
  </main>
</template>
