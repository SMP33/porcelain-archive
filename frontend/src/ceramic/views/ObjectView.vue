<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import http from '../api/http'
import PageThumbGrid from '../components/PageThumbGrid.vue'

const props = defineProps({ id: { type: [String, Number], required: true } })

const object = ref(null)
const loading = ref(true)
const notFound = ref(false)

// Кадры галереи - страницы master-ветки документа-объекта.
const shots = computed(() =>
  (object.value ? object.value.images : []).map((img) => ({
    page_number: img.page,
    image_url: img.url,
    thumb_url: img.thumb_url,
  }))
)

const activeIndex = ref(0)
const activeShot = computed(() => shots.value[activeIndex.value] || null)
const shotLoading = ref(true)

// Указатели, сгруппированные по названию указателя
const pointerGroups = computed(() => {
  const groups = []
  const byId = {}
  for (const p of (object.value && object.value.pointers) || []) {
    if (!byId[p.property_id]) {
      byId[p.property_id] = { id: p.property_id, title: p.property_title, values: [] }
      groups.push(byId[p.property_id])
    }
    byId[p.property_id].values.push(p)
  }
  return groups
})

async function load() {
  loading.value = true
  notFound.value = false
  try {
    const { data } = await http.get(`/api/ceramic/objects/${props.id}`)
    object.value = data
    selectShot(1)
  } catch (err) {
    if (err.response && err.response.status === 404) notFound.value = true
  } finally {
    loading.value = false
  }
}

function selectShot(pageNumber) {
  const idx = shots.value.findIndex((s) => s.page_number === pageNumber)
  activeIndex.value = idx >= 0 ? idx : 0
  shotLoading.value = true
}
function shiftShot(delta) {
  const next = activeIndex.value + delta
  if (next >= 0 && next < shots.value.length) {
    activeIndex.value = next
    shotLoading.value = true
  }
}

onMounted(load)
watch(() => props.id, load)
</script>

<template>
  <div>
    <div v-if="object" class="tw:border-b tw:border-gray-100">
      <div class="tw:max-w-5xl tw:mx-auto tw:px-4 tw:py-2 tw:text-sm tw:text-gray-500 tw:flex tw:items-center tw:gap-2 tw:flex-wrap">
        <router-link to="/objects" class="tw:hover:text-clay-500 tw:transition-colors">Объекты</router-link>
        <span>›</span>
        <span class="tw:text-ink-800">{{ object.name }}</span>
      </div>
    </div>

    <main class="tw:flex-1 tw:max-w-5xl tw:mx-auto tw:px-4 tw:pt-6 tw:pb-16 tw:w-full">
      <div v-if="notFound" class="tw:text-center tw:py-20 tw:text-gray-400">
        <p class="tw:text-lg">Объект не найден</p>
      </div>

      <template v-else-if="object">

        <!-- Шапка: название, описание, указатели -->
        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-clay-100 tw:shadow-sm tw:px-5 tw:py-4 tw:mb-4">
          <div class="tw:flex tw:items-start tw:justify-between tw:gap-6 tw:flex-wrap">
            <h1 class="tw:font-serif tw:font-bold tw:text-xl tw:text-ink-900 tw:leading-snug">{{ object.name }}</h1>
            <dl v-if="pointerGroups.length" class="tw:flex tw:items-start tw:gap-6 tw:text-sm tw:flex-wrap">
              <div v-for="g in pointerGroups" :key="g.id" class="tw:flex tw:items-center tw:gap-2">
                <dt class="tw:text-gray-400">{{ g.title }}:</dt>
                <dd class="tw:flex tw:flex-wrap tw:gap-1.5">
                  <router-link v-for="v in g.values" :key="v.pointer" :to="{ path: '/objects', query: { pointer: v.pointer } }"
                     class="tw:bg-clay-50 tw:text-clay-700 tw:border tw:border-clay-100 tw:rounded-full tw:px-2.5 tw:py-0.5 tw:hover:bg-clay-100 tw:transition-colors">
                    {{ v.value }}
                  </router-link>
                </dd>
              </div>
            </dl>
          </div>
          <p v-if="object.description" class="tw:text-sm tw:text-gray-600 tw:leading-relaxed tw:whitespace-pre-line tw:mt-3">{{ object.description }}</p>
        </div>

        <template v-if="shots.length">
          <!-- Главная фотография -->
          <div class="tw:relative tw:mb-6 tw:flex tw:items-center tw:justify-center"
               style="min-height: 24rem;">
            <div v-if="shotLoading" class="tw:absolute tw:inset-0 tw:flex tw:items-center tw:justify-center">
              <svg class="tw:animate-spin tw:w-9 tw:h-9 tw:text-clay-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="tw:opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="tw:opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
              </svg>
            </div>
            <img v-if="activeShot" :src="activeShot.image_url" :alt="object.name"
                 class="tw:max-w-full tw:object-contain"
                 :style="{ maxHeight: '32rem', opacity: shotLoading ? 0 : 1, transition: 'opacity 0.2s ease' }"
                 @load="shotLoading = false">
          </div>

          <!-- Переключение кадров (стрелки как в карусели на главной) -->
          <div v-if="shots.length > 1" class="tw:flex tw:items-center tw:justify-center tw:gap-6 tw:mb-8 tw:text-ink-900">
            <button @click="shiftShot(-1)" :disabled="activeIndex === 0" aria-label="Предыдущее фото"
                    class="tw:opacity-40 tw:hover:opacity-100 tw:transition-opacity tw:disabled:opacity-10">
              <svg width="100" height="18" viewBox="0 0 100 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                <line x1="100" y1="9" x2="12" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                <polyline points="22,1 10,9 22,17" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <span class="tw:text-sm tw:text-gray-400 tw:tabular-nums">{{ activeIndex + 1 }} / {{ shots.length }}</span>
            <button @click="shiftShot(1)" :disabled="activeIndex >= shots.length - 1" aria-label="Следующее фото"
                    class="tw:opacity-40 tw:hover:opacity-100 tw:transition-opacity tw:disabled:opacity-10">
              <svg width="100" height="18" viewBox="0 0 100 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                <line x1="0" y1="9" x2="88" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                <polyline points="78,1 90,9 78,17" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>

          <!-- Остальные кадры -->
          <PageThumbGrid v-if="shots.length > 1" :pages="shots"
                         :active-number="activeShot && activeShot.page_number"
                         unit="Фото" aspect="4/3" @open="selectShot" />
        </template>

        <div v-else class="stripe-placeholder tw:rounded-lg tw:flex tw:items-center tw:justify-center tw:text-gray-400"
             style="min-height: 24rem;">
          <p class="tw:text-sm tw:bg-white/80 tw:rounded tw:px-3 tw:py-1">Фотографии ещё не загружены</p>
        </div>

      </template>
    </main>
  </div>
</template>
