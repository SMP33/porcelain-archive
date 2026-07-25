<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'
import { useDualRangeSlider } from '../composables/useDualRangeSlider'

const route = useRoute()
const router = useRouter()

const PAGE_SIZE = 21   // кратно трём колонкам сетки

const q = computed(() => route.query.q || '')
const yearFrom = computed(() => route.query.year_from || '')
const yearTo = computed(() => route.query.year_to || '')
const page = computed(() => Math.max(1, parseInt(route.query.page) || 1))

// Выбранные значения указателей (property_enum id) из query.pointer.
const pointers = computed(() => {
  const p = route.query.pointer
  if (!p) return []
  return (Array.isArray(p) ? p : [p]).map(Number).filter((n) => n > 0)
})

const qInput = ref(q.value)
watch(q, (v) => (qInput.value = v))

const results = ref([])
const total = ref(0)
const loading = ref(true)

const facets = ref({ properties: [], year_min: null, year_max: null })

// enum_id -> {value, title указателя} для подписей активных фильтров.
const pointerLabels = computed(() => {
  const m = {}
  for (const p of facets.value.properties || []) {
    for (const v of p.values) m[v.enum_id] = v.value
  }
  return m
})

function togglePointer(enumId) {
  const cur = new Set(pointers.value)
  if (cur.has(enumId)) cur.delete(enumId)
  else cur.add(enumId)
  const arr = [...cur]
  router.push({ query: { ...route.query, pointer: arr.length ? arr : undefined, page: undefined } })
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

function activeFilterParams() {
  const params = {}
  if (q.value) params.q = q.value
  if (yearFrom.value) params.year_from = yearFrom.value
  if (yearTo.value) params.year_to = yearTo.value
  if (pointers.value.length) params.pointer = pointers.value
  return params
}

async function loadResults() {
  loading.value = true
  try {
    const params = { ...activeFilterParams(), offset: (page.value - 1) * PAGE_SIZE, limit: PAGE_SIZE }
    const { data } = await http.get('/api/ceramic/search', { params, paramsSerializer: { indexes: null } })
    results.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadFacets() {
  const { data } = await http.get('/api/ceramic/search/facets', { params: activeFilterParams() })
  facets.value = data
  slider.reset(
    yearFrom.value ? parseInt(yearFrom.value) : data.year_min,
    yearTo.value ? parseInt(yearTo.value) : data.year_max
  )
}

function reload() {
  loadResults()
  loadFacets()
}

onMounted(reload)
watch(
  () => [q.value, yearFrom.value, yearTo.value, pointers.value.join(','), page.value],
  reload
)

const slider = useDualRangeSlider(
  computed(() => facets.value.year_min || 0),
  computed(() => facets.value.year_max || 0),
  0, 0
)

function submitSearch() {
  router.push({ query: { ...route.query, q: qInput.value || undefined, page: undefined } })
}

function submitYearRange() {
  router.push({
    query: { ...route.query, year_from: slider.valueFrom.value, year_to: slider.valueTo.value, page: undefined },
  })
}

function withoutKeys(keys) {
  const query = { ...route.query }
  keys.forEach((k) => delete query[k])
  delete query.page
  return query
}

function goToPage(p) {
  router.push({ query: { ...route.query, page: p } })
}

const hasActiveFilters = computed(
  () => q.value || yearFrom.value || yearTo.value || pointers.value.length
)

// «1958» или «1955–1960» - даты документа для карточки
function formatDates(doc) {
  const from = (doc.date_from || '').slice(0, 4)
  const to = (doc.date_to || '').slice(0, 4)
  if (from && to && from !== to) return `${from}–${to}`
  return from || to || ''
}
</script>

<template>
  <main class="tw:flex-1 tw:max-w-6xl tw:mx-auto tw:px-4 tw:pt-16 tw:pb-16 tw:w-full" style="min-height: calc(100vh - 4rem);">
  <div class="tw:flex tw:gap-8 tw:items-start">

    <!-- Sidebar: filters -->
    <aside class="tw:w-52 tw:shrink-0 tw:sticky tw:top-6 tw:hidden tw:lg:block">

      <form @submit.prevent="submitSearch" class="tw:flex tw:gap-1 tw:mb-6">
        <input v-model="qInput" type="text" placeholder="Поиск…"
               class="tw:flex-1 tw:min-w-0 tw:rounded-lg tw:border tw:border-clay-200 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300 tw:bg-white">
        <button type="submit" class="tw:px-3 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:rounded-lg tw:transition-colors tw:text-sm tw:shrink-0">→</button>
      </form>

      <div v-if="hasActiveFilters" class="tw:mb-5 tw:flex tw:flex-wrap tw:gap-2">
        <router-link v-if="q" :to="{ query: withoutKeys(['q']) }"
           class="tw:inline-flex tw:items-center tw:gap-1 tw:text-xs tw:bg-clay-100 tw:text-clay-700 tw:rounded-full tw:px-2.5 tw:py-1">
          «{{ q }}» <span class="tw:hover:text-clay-900 tw:font-bold tw:leading-none">×</span>
        </router-link>
        <router-link v-if="yearFrom || yearTo" :to="{ query: withoutKeys(['year_from', 'year_to']) }"
           class="tw:inline-flex tw:items-center tw:gap-1 tw:text-xs tw:bg-clay-100 tw:text-clay-700 tw:rounded-full tw:px-2.5 tw:py-1">
          {{ yearFrom || facets.year_min }}–{{ yearTo || facets.year_max }} <span class="tw:hover:text-clay-900 tw:font-bold tw:leading-none">×</span>
        </router-link>
        <button v-for="pid in pointers" :key="pid" type="button" @click="togglePointer(pid)"
           class="tw:inline-flex tw:items-center tw:gap-1 tw:text-xs tw:bg-clay-100 tw:text-clay-700 tw:rounded-full tw:px-2.5 tw:py-1">
          {{ pointerLabels[pid] || pid }} <span class="tw:hover:text-clay-900 tw:font-bold tw:leading-none">×</span>
        </button>
        <router-link to="/materials" class="tw:text-xs tw:text-gray-400 tw:hover:text-gray-600 tw:transition-colors">Сбросить всё</router-link>
      </div>

      <!-- Период -->
      <div v-if="facets.year_min && facets.year_max && facets.year_min !== facets.year_max" class="tw:mb-6">
        <p class="tw:text-xs tw:font-semibold tw:text-gray-400 tw:uppercase tw:tracking-wider tw:mb-3">Период</p>
        <form @submit.prevent="submitYearRange">
          <div class="tw:flex tw:justify-between tw:text-xs tw:text-gray-500 tw:mb-2 tw:font-medium">
            <span>{{ slider.valueFrom.value }}</span>
            <span>{{ slider.valueTo.value }}</span>
          </div>

          <div class="dual-range tw:relative tw:h-4 tw:mb-3">
            <div class="tw:absolute tw:inset-x-0 tw:top-1/2 tw:-translate-y-1/2 tw:h-1 tw:bg-gray-200 tw:rounded-full"></div>
            <div class="tw:absolute tw:top-1/2 tw:-translate-y-1/2 tw:h-1 tw:bg-clay-400 tw:rounded-full" :style="slider.trackStyle.value"></div>
            <input type="range" v-model.number="slider.valueFrom.value" @input="slider.onFromInput"
                   :min="facets.year_min" :max="facets.year_max">
            <input type="range" v-model.number="slider.valueTo.value" @input="slider.onToInput"
                   :min="facets.year_min" :max="facets.year_max">
          </div>

          <button type="submit" class="tw:w-full tw:py-1.5 tw:text-xs tw:rounded-lg tw:border tw:border-clay-200 tw:hover:bg-clay-50 tw:text-gray-600 tw:transition-colors">
            Применить
          </button>
        </form>
      </div>





      <!-- Указатели (из админки) -->
      <div v-for="prop in facets.properties" :key="prop.id" class="tw:mb-6">
        <p class="tw:text-xs tw:font-semibold tw:text-gray-400 tw:uppercase tw:tracking-wider tw:mb-2">{{ prop.title }}</p>
        <ul class="tw:space-y-0.5">
          <li v-for="v in prop.values" :key="v.enum_id">
            <button type="button" @click="togglePointer(v.enum_id)"
               class="tw:w-full tw:flex tw:items-center tw:justify-between tw:px-2 tw:py-1 tw:rounded-lg tw:text-sm tw:transition-colors tw:text-left"
               :class="pointers.includes(v.enum_id) ? 'tw:bg-clay-100 tw:text-clay-700 tw:font-medium' : 'tw:text-gray-600 tw:hover:bg-gray-100'">
              <span class="tw:truncate">{{ v.value }}</span>
              <span class="tw:text-xs tw:text-gray-400 tw:shrink-0 tw:ml-1">{{ v.count }}</span>
            </button>
          </li>
        </ul>
      </div>

    </aside>

    <!-- Main: results -->
    <div class="tw:flex-1 tw:min-w-0">

      <form @submit.prevent="submitSearch" class="tw:flex tw:gap-2 tw:mb-4 tw:lg:hidden">
        <input v-model="qInput" type="text" placeholder="Поиск по документам…"
               class="tw:flex-1 tw:rounded-lg tw:border tw:border-clay-200 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300 tw:bg-white">
        <button type="submit" class="tw:px-4 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:rounded-lg tw:transition-colors tw:text-sm">→</button>
      </form>

      <div class="tw:flex tw:items-baseline tw:justify-between tw:mb-4">
        <h1 class="tw:font-serif tw:text-2xl tw:font-bold tw:text-ink-900">{{ q ? 'Результаты поиска' : 'Материалы' }}</h1>
        <span class="tw:text-sm tw:text-gray-400">{{ total }}</span>
      </div>

      <div v-if="results.length" class="tw:grid tw:grid-cols-1 tw:sm:grid-cols-2 tw:xl:grid-cols-3 tw:gap-5 tw:content-start">
        <router-link v-for="doc in results" :key="doc.id" :to="`/document/${doc.id}`"
           class="tw:group tw:bg-white tw:rounded-lg tw:border tw:border-clay-100 tw:shadow-sm tw:hover:shadow-md tw:hover:border-clay-200 tw:transition-all tw:overflow-hidden tw:flex tw:flex-col">

          <div class="tw:relative tw:overflow-hidden tw:bg-gray-100 tw:shrink-0" style="aspect-ratio:1/1">
            <img v-if="doc.thumb_url" :src="doc.thumb_url" :alt="doc.title" loading="lazy"
                 class="tw:w-full tw:h-full tw:object-cover tw:object-top tw:group-hover:scale-105 tw:transition-transform tw:duration-300">
            <div v-else class="stripe-placeholder tw:w-full tw:h-full"></div>
            <span v-if="doc.page_count"
                  class="tw:absolute tw:bottom-2 tw:right-2 tw:text-xs tw:text-white tw:bg-black/50 tw:rounded-full tw:px-2 tw:py-0.5">
              {{ doc.page_count }} стр.
            </span>
          </div>

          <div class="tw:p-4 tw:flex tw:flex-col tw:gap-1.5">
            <h2 class="tw:font-serif tw:font-semibold tw:text-base tw:text-ink-900 tw:group-hover:text-clay-500 tw:transition-colors tw:leading-snug"
                >{{ doc.title }}</h2>
            <p v-if="formatDates(doc)" class="tw:text-xs tw:text-gray-400">{{ formatDates(doc) }}</p>
            <p v-if="doc.description" class="tw:text-sm tw:text-gray-500 tw:line-clamp-2">{{ doc.description }}</p>
            <div v-if="doc.pointers && doc.pointers.length" class="tw:flex tw:flex-wrap tw:gap-1 tw:mt-1">
              <span v-for="p in doc.pointers" :key="p.enum_id"
                    class="tw:text-xs tw:bg-clay-50 tw:text-clay-700 tw:border tw:border-clay-100 tw:rounded-full tw:px-2 tw:py-0.5">
                {{ p.value }}
              </span>
            </div>
          </div>
        </router-link>

      </div>

      <div v-if="results.length && totalPages > 1" class="tw:mt-8 tw:flex tw:justify-center tw:items-center tw:gap-2 tw:text-sm">
        <button v-if="page > 1" @click="goToPage(page - 1)"
           class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-clay-200 tw:hover:bg-clay-50 tw:transition-colors">← Назад</button>
        <span class="tw:text-gray-500">{{ page }} / {{ totalPages }}</span>
        <button v-if="page < totalPages" @click="goToPage(page + 1)"
           class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-clay-200 tw:hover:bg-clay-50 tw:transition-colors">Вперёд →</button>
      </div>

      <div v-else-if="!loading && q" class="tw:text-center tw:py-20 tw:text-gray-400">
        <div class="tw:text-4xl tw:mb-3">🔍</div>
        <p>Ничего не найдено по запросу «{{ q }}»</p>
        <p class="tw:text-sm tw:mt-1">Попробуйте изменить запрос или сбросить фильтры</p>
      </div>
      <div v-else-if="!loading && !results.length" class="tw:text-center tw:py-20 tw:text-gray-400">
        <div class="tw:text-4xl tw:mb-3">📄</div>
        <p>Материалы ещё не добавлены</p>
      </div>

    </div>
  </div>
  </main>
</template>

<style scoped>
.dual-range input[type=range] {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  background: transparent;
  pointer-events: none;
  -webkit-appearance: none;
  appearance: none;
}
.dual-range input[type=range]::-webkit-slider-thumb {
  pointer-events: all;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: #dc2626;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,.25);
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
}
.dual-range input[type=range]::-moz-range-thumb {
  pointer-events: all;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: #dc2626;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,.25);
  cursor: pointer;
  appearance: none;
}
.dual-range input[type=range]::-webkit-slider-runnable-track { background: transparent; }
.dual-range input[type=range]::-moz-range-track { background: transparent; }
</style>
