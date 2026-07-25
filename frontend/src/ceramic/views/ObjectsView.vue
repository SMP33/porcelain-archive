<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'
import teapotIcon from '../assets/img/teapot-icon.png'

const route = useRoute()
const router = useRouter()

const q = computed(() => route.query.q || '')
const qInput = ref(q.value)
watch(q, (v) => (qInput.value = v))

// Выбранные значения указателей ("tag:value") из query.pointer.
const pointers = computed(() => {
  const p = route.query.pointer
  if (!p) return []
  return (Array.isArray(p) ? p : [p]).filter(Boolean)
})

const objects = ref([])
const loading = ref(true)
const properties = ref([])

// pointer ("tag:value") -> значение указателя (подписи активных фильтров)
const pointerLabels = computed(() => {
  const m = {}
  for (const p of properties.value) {
    for (const v of p.values) m[v.pointer] = v.value
  }
  return m
})

function activeParams() {
  const params = {}
  if (q.value) params.q = q.value
  if (pointers.value.length) params.pointer = pointers.value
  return params
}

async function load() {
  loading.value = true
  try {
    const { data } = await http.get('/api/ceramic/objects', {
      params: activeParams(),
      paramsSerializer: { indexes: null },
    })
    objects.value = data.items
  } finally {
    loading.value = false
  }
}

async function loadFacets() {
  const { data } = await http.get('/api/ceramic/objects/facets')
  properties.value = data.properties
}

onMounted(() => {
  load()
  loadFacets()
})
watch(() => [q.value, pointers.value.join(',')], load)

function submitSearch() {
  router.push({ query: { ...route.query, q: qInput.value || undefined } })
}

function togglePointer(pointer) {
  const cur = new Set(pointers.value)
  if (cur.has(pointer)) cur.delete(pointer)
  else cur.add(pointer)
  const arr = [...cur]
  router.push({ query: { ...route.query, pointer: arr.length ? arr : undefined } })
}

function withoutKeys(keys) {
  const query = { ...route.query }
  keys.forEach((k) => delete query[k])
  return query
}

const hasActiveFilters = computed(() => !!q.value || pointers.value.length > 0)
</script>

<template>
  <main class="tw:flex-1 tw:max-w-6xl tw:mx-auto tw:px-4 tw:pt-16 tw:pb-8 tw:w-full" style="min-height: calc(100vh - 4rem);">
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
        <button v-for="pid in pointers" :key="pid" type="button" @click="togglePointer(pid)"
           class="tw:inline-flex tw:items-center tw:gap-1 tw:text-xs tw:bg-clay-100 tw:text-clay-700 tw:rounded-full tw:px-2.5 tw:py-1">
          {{ pointerLabels[pid] || pid }} <span class="tw:hover:text-clay-900 tw:font-bold tw:leading-none">×</span>
        </button>
        <router-link to="/objects" class="tw:text-xs tw:text-gray-400 tw:hover:text-gray-600 tw:transition-colors">Сбросить всё</router-link>
      </div>

      <!-- Указатели (из админки) -->
      <div v-for="prop in properties" :key="prop.id" class="tw:mb-6">
        <p class="tw:text-xs tw:font-semibold tw:text-gray-400 tw:uppercase tw:tracking-wider tw:mb-2">{{ prop.title }}</p>
        <ul class="tw:space-y-0.5">
          <li v-for="v in prop.values" :key="v.pointer">
            <button type="button" @click="togglePointer(v.pointer)"
               class="tw:w-full tw:flex tw:items-center tw:justify-between tw:px-2 tw:py-1 tw:rounded-lg tw:text-sm tw:transition-colors tw:text-left"
               :class="pointers.includes(v.pointer) ? 'tw:bg-clay-100 tw:text-clay-700 tw:font-medium' : 'tw:text-gray-600 tw:hover:bg-gray-100'">
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
        <input v-model="qInput" type="text" placeholder="Поиск по объектам…"
               class="tw:flex-1 tw:rounded-lg tw:border tw:border-clay-200 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300 tw:bg-white">
        <button type="submit" class="tw:px-4 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:rounded-lg tw:transition-colors tw:text-sm">→</button>
      </form>

      <div class="tw:flex tw:items-baseline tw:justify-between tw:mb-4">
        <h1 class="tw:font-serif tw:text-2xl tw:font-bold tw:text-ink-900">Объекты</h1>
        <span class="tw:text-sm tw:text-gray-400">{{ objects.length }}</span>
      </div>

      <div v-if="objects.length" class="tw:grid tw:grid-cols-1 tw:sm:grid-cols-2 tw:xl:grid-cols-3 tw:gap-5">
        <router-link v-for="o in objects" :key="o.id" :to="`/objects/${o.id}`"
           class="tw:group tw:bg-white tw:rounded-lg tw:border tw:border-clay-100 tw:shadow-sm tw:hover:shadow-md tw:hover:border-clay-200 tw:transition-all tw:overflow-hidden tw:flex tw:flex-col">

          <div class="tw:relative tw:overflow-hidden tw:bg-gray-100 tw:shrink-0" style="aspect-ratio:1/1">
            <img v-if="o.cover_url" :src="o.cover_url" :alt="o.name"
                 class="tw:w-full tw:h-full tw:object-cover tw:group-hover:scale-105 tw:transition-transform tw:duration-300">
            <div v-else class="stripe-placeholder tw:w-full tw:h-full"></div>
            <span v-if="o.page_count > 1"
                  class="tw:absolute tw:bottom-2 tw:right-2 tw:text-xs tw:text-white tw:bg-black/50 tw:rounded-full tw:px-2 tw:py-0.5">
              {{ o.page_count }} фото
            </span>
          </div>

          <div class="tw:p-4 tw:flex tw:flex-col tw:gap-1.5">
            <h2 class="tw:font-serif tw:font-semibold tw:text-base tw:text-ink-900 tw:group-hover:text-clay-500 tw:transition-colors tw:leading-snug">
              {{ o.name }}
            </h2>
            <p v-if="o.description" class="tw:text-sm tw:text-gray-500 tw:line-clamp-2">{{ o.description }}</p>
            <div v-if="o.pointers.length" class="tw:flex tw:flex-wrap tw:gap-1 tw:mt-1">
              <span v-for="p in o.pointers" :key="p.pointer"
                    class="tw:text-xs tw:bg-clay-50 tw:text-clay-700 tw:border tw:border-clay-100 tw:rounded-full tw:px-2 tw:py-0.5">
                {{ p.value }}
              </span>
            </div>
          </div>
        </router-link>
      </div>

      <div v-else-if="!loading && hasActiveFilters" class="tw:text-center tw:py-20 tw:text-gray-400">
        <div class="tw:text-4xl tw:mb-3">🔍</div>
        <p>Ничего не найдено</p>
        <p class="tw:text-sm tw:mt-1">Попробуйте изменить запрос или сбросить фильтры</p>
      </div>
      <div v-else-if="!loading" class="tw:text-center tw:py-20 tw:text-gray-300">
        <img :src="teapotIcon" alt="" class="tw:w-16 tw:h-16 tw:mx-auto tw:mb-4 tw:opacity-25">
        <p class="tw:text-lg">Объекты ещё не добавлены</p>
      </div>

    </div>
  </div>
  </main>
</template>
