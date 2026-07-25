<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import http from '../api/http'
import PageThumbGrid from '../components/PageThumbGrid.vue'

const props = defineProps({ id: { type: [String, Number], required: true } })

const doc = ref(null)
const pages = ref([])
const branchId = ref(null)

async function load() {
  const { data: docData } = await http.get(`/api/documents/${props.id}`)
  const { data: branchData } = await http.get(`/api/documents/${props.id}/master_branch_id`)
  branchId.value = branchData.branch_id
  const { data: countData } = await http.get(`/api/documents/branches/${branchId.value}/pages/count`)
  const count = countData.count

  doc.value = {
    title: docData.name,
    author: docData.author,
    description: docData.description,
    page_count: count,
  }

  pages.value = Array.from({ length: count }, (_, i) => {
    const pos = i + 1
    return {
      page_number: pos,
      // Для миниатюр используется полноразмерное (web) изображение, а не крошечный
      // preview (139x200) - иначе миниатюры размыты. Грузятся лениво (loading=lazy).
      thumb_url: `/api/documents/branches/${branchId.value}/pages/${pos}/image`,
      image_url: `/api/documents/branches/${branchId.value}/pages/${pos}/image`,
      text_url: `/api/documents/branches/${branchId.value}/pages/${pos}/text`,
      text: undefined, // не загружено; null - загружено, но текста нет
    }
  })
  viewerIndex.value = 0
  afterPageChange()
}
onMounted(load)
watch(() => props.id, load)

// Ленивая загрузка текста страницы (блоки с координатами)
async function loadPageText(page) {
  if (page.text !== undefined) return
  try {
    const { data } = await http.get(page.text_url)
    page.text = data.text || null
  } catch {
    page.text = null
  }
}

// Соединённый текст блоков страницы (по порядку seq)
function pagePlainText(page) {
  if (!page || !page.text || !page.text.blocks) return ''
  return page.text.blocks
    .slice()
    .sort((a, b) => (a.seq || 0) - (b.seq || 0))
    .map((b) => b.text)
    .join('\n')
    .trim()
}

// --- Просмотрщик ---
const MIN_SCALE = 1
const MAX_SCALE = 6

const viewerIndex = ref(0)
const viewerPage = computed(() => pages.value[viewerIndex.value] || null)
const viewerLoading = ref(true)

const scale = ref(1)
const panX = ref(0)
const panY = ref(0)
const rotation = ref(0)

// Рамка изображения всегда в ориентации ТЕКСТОВОГО слоя (pageAspect) - в ней же
// лежат overlay-блоки (в % от рамки), поэтому координаты всегда корректны.
// Если сам скан повёрнут относительно текста (файлы бывают portrait-холстом с
// боковым содержимым при landscape-тексте), изображение доворачивается на 90°.
const imgNatural = ref({ w: 0, h: 0 })
const rotateFix = ref(-90) // сторона доворота скана (правится, если развернёт не туда)
function onImgLoad(e) {
  imgNatural.value = { w: e.target.naturalWidth, h: e.target.naturalHeight }
  viewerLoading.value = false
}
const frameAspect = computed(() => pageAspect.value)
// Скан нужно довернуть, если его ориентация не совпадает с ориентацией текста
const needRotate = computed(() => {
  const { w, h } = imgNatural.value
  if (!w || !h) return false
  return (w >= h) !== (pageAspect.value >= 1)
})
const rotorStyle = computed(() => {
  if (!needRotate.value) return { width: '100%', height: '100%' }
  // Повёрнутый скан: контейнер с переставленными сторонами рамки (в % от рамки,
  // чтобы адаптироваться к любому её размеру), затем rotate 90° -> заполняет рамку.
  const a = pageAspect.value
  return {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: (100 / a) + '%',
    height: (a * 100) + '%',
    transform: `translate(-50%, -50%) rotate(${rotateFix.value}deg)`,
  }
})

const wrapperTransform = computed(() => ({
  transform: `translate(${panX.value}px, ${panY.value}px) scale(${scale.value}) rotate(${rotation.value}deg)`,
  cursor: scale.value > 1 ? 'grab' : 'default',
}))
const zoomPercent = computed(() => Math.round(scale.value * 100))
const canZoomIn = computed(() => scale.value < MAX_SCALE)
const canZoomOut = computed(() => scale.value > MIN_SCALE)

function resetView() {
  scale.value = 1
  panX.value = 0
  panY.value = 0
  rotation.value = 0
}
function zoomBy(delta) {
  scale.value = Math.min(MAX_SCALE, Math.max(MIN_SCALE, +(scale.value + delta).toFixed(2)))
  if (scale.value === 1) { panX.value = 0; panY.value = 0 }
}
function rotateBy(deg) { rotation.value = (rotation.value + deg) % 360 }
function onWheel(e) { e.preventDefault(); zoomBy(e.deltaY < 0 ? 0.2 : -0.2) }
function onDblclick() { if (scale.value !== 1) resetView(); else scale.value = 2.5 }

let panning = false
let startX = 0, startY = 0, originX = 0, originY = 0
function onMousedown(e) {
  if (scale.value <= 1) return
  panning = true
  startX = e.clientX; startY = e.clientY
  originX = panX.value; originY = panY.value
  e.preventDefault()
}
function onMousemove(e) {
  if (!panning) return
  panX.value = originX + (e.clientX - startX)
  panY.value = originY + (e.clientY - startY)
}
function onMouseup() { panning = false }

function afterPageChange() {
  viewerLoading.value = true
  resetView()
  hoveredBlock.value = null
  if (viewerPage.value) loadPageText(viewerPage.value)
}
function selectPage(pageNumber) {
  const idx = pages.value.findIndex((p) => p.page_number === pageNumber)
  if (idx >= 0 && idx !== viewerIndex.value) { viewerIndex.value = idx; afterPageChange() }
}
function viewerShift(delta) {
  const next = viewerIndex.value + delta
  if (next >= 0 && next < pages.value.length) { viewerIndex.value = next; afterPageChange() }
}

// --- Режимы расшифровки ---
// none - без расшифровки; side - текст справа; overlay - блоки поверх скана;
// map - документ + белая схема блоков по координатам с двусторонней подсветкой
const viewMode = ref('none')
watch(viewMode, () => { if (viewerPage.value) loadPageText(viewerPage.value) })

const currentBlocks = computed(() => {
  const p = viewerPage.value
  if (!p || !p.text || !p.text.blocks) return []
  return p.text.blocks.slice().sort((a, b) => (a.seq || 0) - (b.seq || 0))
})
// Пропорции страницы (для белого листа-схемы в режиме map)
const pageAspect = computed(() => {
  const t = viewerPage.value && viewerPage.value.text
  if (!t || !t.width || !t.height) return 0.7
  return t.width / t.height
})
// Индекс блока под курсором - подсвечивается синхронно на документе и на схеме
const hoveredBlock = ref(null)
const currentPlainText = computed(() => pagePlainText(viewerPage.value))


const copied = ref(false)
function copyCurrent() {
  navigator.clipboard.writeText(currentPlainText.value).then(() => {
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  })
}

// --- Полный текст документа ---
const fullTextOpen = ref(false)
const fullTextLoading = ref(false)
const fullText = ref([])
async function openFullText() {
  fullTextOpen.value = true
  fullTextLoading.value = true
  await Promise.all(pages.value.map((p) => loadPageText(p)))
  fullText.value = pages.value.map((p) => ({ page_number: p.page_number, text: pagePlainText(p) }))
  fullTextLoading.value = false
}
const fullTextCopied = ref(false)
function copyFullText() {
  const joined = fullText.value
    .filter((p) => p.text)
    .map((p) => `— Стр. ${p.page_number} —\n${p.text}`)
    .join('\n\n')
  navigator.clipboard.writeText(joined).then(() => {
    fullTextCopied.value = true
    setTimeout(() => (fullTextCopied.value = false), 1500)
  })
}

onMounted(() => {
  document.addEventListener('mousemove', onMousemove)
  document.addEventListener('mouseup', onMouseup)
})
onUnmounted(() => {
  document.removeEventListener('mousemove', onMousemove)
  document.removeEventListener('mouseup', onMouseup)
})
</script>

<template>
  <div v-if="doc">
    <div class="tw:border-b tw:border-gray-100">
      <div class="tw:max-w-7xl tw:mx-auto tw:px-4 tw:py-2 tw:text-sm tw:text-gray-500 tw:flex tw:items-center tw:gap-2 tw:flex-wrap">
        <router-link to="/materials" class="tw:hover:text-clay-500 tw:transition-colors">Материалы</router-link>
        <span>›</span>
        <span class="tw:text-ink-800">{{ doc.title }}</span>
      </div>
    </div>

    <main class="tw:flex-1 tw:max-w-7xl tw:mx-auto tw:px-4 tw:pt-6 tw:pb-16 tw:w-full">

      <!-- Метаданные горизонтально сверху -->
      <div class="tw:bg-white tw:rounded-xl tw:border tw:border-clay-100 tw:shadow-sm tw:px-5 tw:py-4 tw:mb-4">
        <div class="tw:flex tw:items-center tw:justify-between tw:gap-4 tw:flex-wrap">
          <h1 class="tw:font-serif tw:font-bold tw:text-xl tw:text-ink-900 tw:leading-snug">{{ doc.title }}</h1>
          <dl class="tw:flex tw:items-center tw:gap-6 tw:text-sm">
            <div v-if="doc.page_count" class="tw:flex tw:items-center tw:gap-1.5">
              <dt class="tw:text-gray-400">Страниц:</dt>
              <dd class="tw:text-ink-800 tw:font-medium">{{ doc.page_count }}</dd>
            </div>
            <div v-if="doc.author" class="tw:flex tw:items-center tw:gap-1.5">
              <dt class="tw:text-gray-400">Автор:</dt>
              <dd class="tw:text-ink-800 tw:font-medium">{{ doc.author }}</dd>
            </div>
          </dl>
        </div>
        <p v-if="doc.description" class="tw:text-sm tw:text-gray-600 tw:leading-relaxed tw:whitespace-pre-line tw:mt-3">{{ doc.description }}</p>
      </div>

      <template v-if="pages.length">
        <!-- Тулбар просмотрщика -->
        <div class="tw:bg-white tw:rounded-t-xl tw:border tw:border-clay-100 tw:shadow-sm tw:px-4 tw:py-2.5 tw:flex tw:items-center tw:justify-between tw:gap-3 tw:flex-wrap">
          <!-- Навигация страниц -->
          <div class="tw:flex tw:items-center tw:gap-2">
            <button @click="viewerShift(-1)" :disabled="viewerIndex === 0"
                    class="tw:px-2.5 tw:py-1 tw:text-sm tw:rounded tw:border tw:border-clay-200 tw:text-gray-600 tw:hover:bg-clay-50 tw:transition-colors tw:disabled:opacity-30">←</button>
            <span class="tw:text-sm tw:text-gray-500 tw:tabular-nums">Стр. {{ viewerIndex + 1 }} из {{ pages.length }}</span>
            <button @click="viewerShift(1)" :disabled="viewerIndex >= pages.length - 1"
                    class="tw:px-2.5 tw:py-1 tw:text-sm tw:rounded tw:border tw:border-clay-200 tw:text-gray-600 tw:hover:bg-clay-50 tw:transition-colors tw:disabled:opacity-30">→</button>
          </div>

          <!-- Zoom / rotate -->
          <div class="tw:flex tw:items-center tw:gap-1.5">
            <span class="tw:inline-flex tw:items-center tw:rounded tw:border tw:border-clay-200 tw:overflow-hidden">
              <button @click="zoomBy(-0.5)" :disabled="!canZoomOut" aria-label="Уменьшить"
                      class="tw:px-2.5 tw:py-1 tw:text-base tw:leading-none tw:text-gray-600 tw:hover:bg-clay-50 tw:transition-colors tw:disabled:opacity-30">−</button>
              <button @click="resetView" title="Сбросить"
                      class="tw:px-2 tw:py-1 tw:text-xs tw:text-gray-500 tw:hover:bg-clay-50 tw:transition-colors tw:tabular-nums tw:min-w-[3rem]">{{ zoomPercent }}%</button>
              <button @click="zoomBy(0.5)" :disabled="!canZoomIn" aria-label="Увеличить"
                      class="tw:px-2.5 tw:py-1 tw:text-base tw:leading-none tw:text-gray-600 tw:hover:bg-clay-50 tw:transition-colors tw:disabled:opacity-30">+</button>
            </span>
            <button @click="rotateBy(-90)" title="Повернуть влево"
                    class="tw:px-2.5 tw:py-1 tw:text-sm tw:rounded tw:border tw:border-clay-200 tw:text-gray-600 tw:hover:bg-clay-50 tw:transition-colors">↺</button>
            <button @click="rotateBy(90)" title="Повернуть вправо"
                    class="tw:px-2.5 tw:py-1 tw:text-sm tw:rounded tw:border tw:border-clay-200 tw:text-gray-600 tw:hover:bg-clay-50 tw:transition-colors">↻</button>
          </div>

          <!-- Режим расшифровки + полный текст -->
          <div class="tw:flex tw:items-center tw:gap-2">
            <span class="tw:inline-flex tw:items-center tw:rounded tw:border tw:border-clay-200 tw:overflow-hidden tw:text-sm">
              <button @click="viewMode = 'none'" title="Без расшифровки"
                      class="tw:px-3 tw:py-1 tw:transition-colors"
                      :class="viewMode === 'none' ? 'tw:bg-clay-500 tw:text-white' : 'tw:text-gray-600 tw:hover:bg-clay-50'">Без текста</button>
              <button @click="viewMode = 'overlay'" title="Расшифровка поверх документа"
                      class="tw:px-3 tw:py-1 tw:border-l tw:border-clay-200 tw:transition-colors"
                      :class="viewMode === 'overlay' ? 'tw:bg-clay-500 tw:text-white' : 'tw:text-gray-600 tw:hover:bg-clay-50'">Поверх</button>
              <button @click="viewMode = 'map'" title="Схема текста рядом с документом"
                      class="tw:px-3 tw:py-1 tw:border-l tw:border-clay-200 tw:transition-colors"
                      :class="viewMode === 'map' ? 'tw:bg-clay-500 tw:text-white' : 'tw:text-gray-600 tw:hover:bg-clay-50'">Схема</button>
              <button @click="viewMode = 'side'" title="Расшифровка рядом"
                      class="tw:px-3 tw:py-1 tw:border-l tw:border-clay-200 tw:transition-colors"
                      :class="viewMode === 'side' ? 'tw:bg-clay-500 tw:text-white' : 'tw:text-gray-600 tw:hover:bg-clay-50'">Расшифровка</button>
            </span>
            <a v-if="viewerPage" :href="viewerPage.image_url" target="_blank"
               class="tw:px-3 tw:py-1 tw:text-sm tw:rounded tw:border tw:border-clay-200 tw:text-gray-600 tw:hover:bg-clay-50 tw:transition-colors">
              Оригинал ↗
            </a>
            <button @click="openFullText"
                    class="tw:px-3 tw:py-1 tw:text-sm tw:rounded tw:border tw:border-clay-200 tw:text-gray-600 tw:hover:bg-clay-50 tw:transition-colors">
              Полный текст
            </button>
          </div>
        </div>

        <!-- Область: изображение (+ overlay) слева, расшифровка справа.
             Полосатый фон на родителе - чтобы полосы шли непрерывно через
             просмотрщик и пустую правую колонку (в режимах без панели). -->
        <div class="tw:rounded-b-xl tw:border tw:border-t-0 tw:border-clay-100 tw:shadow-sm tw:overflow-hidden tw:mb-6 tw:flex tw:flex-col tw:lg:flex-row"
             style="background-image: repeating-linear-gradient(135deg, #f1f1f2 0, #f1f1f2 18px, #ffffff 18px, #ffffff 36px);">

          <!-- Просмотрщик -->
          <div class="tw:relative tw:flex tw:items-center tw:justify-center tw:overflow-hidden tw:select-none tw:flex-1 tw:min-w-0"
               style="min-height: 65vh; max-height: 82vh;">
            <div v-if="viewerLoading" class="tw:absolute tw:inset-0 tw:flex tw:items-center tw:justify-center">
              <svg class="tw:animate-spin tw:w-9 tw:h-9 tw:text-clay-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="tw:opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="tw:opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
              </svg>
            </div>
            <!-- Рамка = трансформируемый элемент (zoom/pan/rotate) в ориентации
                 текстового слоя, вписанная целиком в область (min по ширине и высоте).
                 Скан доворачивается при рассинхроне, overlay-блоки (% от рамки) точны. -->
            <div class="tw:relative tw:overflow-hidden"
                 :style="{ ...wrapperTransform, transformOrigin: 'center center', transition: 'transform 0.05s linear',
                           width: `min(100%, calc(82vh * ${frameAspect}))`, aspectRatio: frameAspect }"
                 @wheel="onWheel" @dblclick="onDblclick" @mousedown="onMousedown">
              <div :style="rotorStyle">
                <img v-if="viewerPage" :src="viewerPage.image_url" :alt="`Страница ${viewerPage.page_number}`" draggable="false"
                     class="tw:block tw:w-full tw:h-full tw:object-contain"
                     :style="{ opacity: viewerLoading ? 0 : 1, transition: 'opacity 0.2s ease' }"
                     @load="onImgLoad">
              </div>
              <!-- Overlay: блоки текста по координатам документа -->
              <div v-if="viewMode === 'overlay' && viewerPage && viewerPage.text" class="tw:absolute tw:inset-0 tw:pointer-events-none">
                <div v-for="(b, i) in currentBlocks" :key="i"
                     class="tw:absolute tw:pointer-events-auto tw:overflow-hidden tw:bg-amber-100/80 tw:border tw:border-amber-400/70 tw:rounded-sm tw:text-[0.6rem] tw:leading-tight tw:text-ink-900 tw:px-0.5"
                     :style="{ left: b.rect.x + '%', top: b.rect.y + '%', width: b.rect.width + '%', height: b.rect.height + '%' }"
                     :title="b.text">
                  <span class="tw:whitespace-pre-wrap">{{ b.text }}</span>
                </div>
              </div>
              <!-- Map: интерактивные зоны блоков на документе (подсветка синхронно со схемой) -->
              <div v-if="viewMode === 'map' && viewerPage && viewerPage.text" class="tw:absolute tw:inset-0 tw:pointer-events-none">
                <div v-for="(b, i) in currentBlocks" :key="i"
                     class="tw:absolute tw:pointer-events-auto tw:rounded-sm tw:border tw:transition-colors tw:cursor-pointer"
                     :class="hoveredBlock === i ? 'tw:bg-amber-300/50 tw:border-amber-500' : 'tw:border-amber-400/50 tw:hover:bg-amber-200/30'"
                     :style="{ left: b.rect.x + '%', top: b.rect.y + '%', width: b.rect.width + '%', height: b.rect.height + '%' }"
                     @mouseenter="hoveredBlock = i" @mouseleave="hoveredBlock = null"></div>
              </div>
            </div>
          </div>

          <!-- Правая колонка присутствует всегда (фикс. ширина) - это фиксирует
               ширину области документа, чтобы страница не двигалась при смене
               режима. Содержимое зависит от режима; в none/overlay - пустая. -->
          <aside class="tw:w-full tw:lg:w-[28rem] tw:shrink-0 tw:border-t tw:lg:border-t-0 tw:lg:border-l tw:flex tw:flex-col"
                 :class="(viewMode === 'side' || viewMode === 'map') ? 'tw:border-clay-100 tw:bg-gray-50' : 'tw:border-transparent tw:bg-transparent'"
                 style="max-height: 82vh;">

            <!-- Режим "Расшифровка": текст страницы -->
            <template v-if="viewMode === 'side'">
              <div class="tw:flex tw:items-center tw:justify-between tw:px-4 tw:py-2.5 tw:border-b tw:border-clay-100">
                <span class="tw:text-sm tw:font-semibold tw:text-ink-900">Расшифровка · стр. {{ viewerIndex + 1 }}</span>
                <button v-if="currentPlainText" @click="copyCurrent"
                        class="tw:text-xs tw:text-clay-500 tw:hover:text-clay-400 tw:transition-colors">
                  {{ copied ? 'Скопировано' : 'Копировать' }}
                </button>
              </div>
              <div class="tw:flex-1 tw:overflow-auto tw:p-4 tw:bg-white">
                <p v-if="currentPlainText" class="tw:text-sm tw:text-ink-800 tw:leading-relaxed tw:whitespace-pre-wrap">{{ currentPlainText }}</p>
                <p v-else class="tw:text-sm tw:text-gray-400">Для этой страницы расшифровка отсутствует.</p>
              </div>
            </template>

            <!-- Режим "Схема": белый лист с блоками по координатам -->
            <template v-else-if="viewMode === 'map'">
              <div class="tw:flex tw:items-center tw:justify-between tw:gap-2 tw:px-4 tw:py-2.5 tw:border-b tw:border-clay-100">
                <span class="tw:text-sm tw:font-semibold tw:text-ink-900">Схема текста · стр. {{ viewerIndex + 1 }}</span>
              </div>
              <div class="tw:flex-1 tw:overflow-auto tw:p-4 tw:flex tw:justify-center tw:items-start">
                <div v-if="viewerPage && viewerPage.text && currentBlocks.length"
                     class="tw:relative tw:bg-white tw:shadow-sm tw:border tw:border-gray-200 tw:w-full"
                     :style="{ aspectRatio: pageAspect }">
                  <div v-for="(b, i) in currentBlocks" :key="i"
                       class="tw:absolute tw:overflow-hidden tw:rounded-sm tw:border tw:px-0.5 tw:text-[0.55rem] tw:leading-tight tw:text-ink-900 tw:cursor-pointer tw:transition-colors"
                       :class="hoveredBlock === i ? 'tw:bg-amber-200 tw:border-amber-500' : 'tw:bg-amber-50 tw:border-amber-200 tw:hover:bg-amber-100'"
                       :style="{ left: b.rect.x + '%', top: b.rect.y + '%', width: b.rect.width + '%', height: b.rect.height + '%' }"
                       :title="b.text"
                       @mouseenter="hoveredBlock = i" @mouseleave="hoveredBlock = null">
                    <span class="tw:whitespace-pre-wrap">{{ b.text }}</span>
                  </div>
                </div>
                <p v-else class="tw:text-sm tw:text-gray-400 tw:self-start">Для этой страницы расшифровка отсутствует.</p>
              </div>
            </template>
          </aside>
        </div>

        <!-- Миниатюры на всю ширину -->
        <p class="tw:text-sm tw:text-gray-400 tw:mb-3">{{ pages.length }} стр. — выберите страницу для просмотра</p>
        <PageThumbGrid :pages="pages" :active-number="viewerPage && viewerPage.page_number" @open="selectPage" />
      </template>

      <div v-else class="tw:flex tw:flex-col tw:items-center tw:justify-center tw:py-24 tw:text-gray-300">
        <svg xmlns="http://www.w3.org/2000/svg" class="tw:w-16 tw:h-16 tw:mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14
                   M8 6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
        </svg>
        <p class="tw:text-sm">Страницы ещё не загружены</p>
      </div>
    </main>

    <!-- Модалка полного текста документа -->
    <div v-if="fullTextOpen" class="tw:fixed tw:inset-0 tw:bg-black/50 tw:z-50 tw:flex tw:items-center tw:justify-center tw:p-4" @click="fullTextOpen = false">
      <div class="tw:bg-white tw:rounded-xl tw:shadow-2xl tw:max-w-3xl tw:w-full tw:max-h-[85vh] tw:flex tw:flex-col" @click.stop>
        <div class="tw:flex tw:items-center tw:justify-between tw:px-5 tw:py-3 tw:border-b tw:border-gray-200">
          <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900">Полный текст · {{ doc.title }}</h2>
          <div class="tw:flex tw:items-center tw:gap-3">
            <button v-if="!fullTextLoading" @click="copyFullText" class="tw:text-sm tw:text-clay-500 tw:hover:text-clay-400 tw:transition-colors">
              {{ fullTextCopied ? 'Скопировано' : 'Копировать всё' }}
            </button>
            <button @click="fullTextOpen = false" class="tw:text-gray-400 tw:hover:text-gray-600 tw:transition-colors tw:text-xl tw:leading-none">✕</button>
          </div>
        </div>
        <div class="tw:flex-1 tw:overflow-auto tw:p-5">
          <div v-if="fullTextLoading" class="tw:text-center tw:py-16 tw:text-gray-400">
            <svg class="tw:animate-spin tw:w-8 tw:h-8 tw:mx-auto tw:mb-3 tw:text-clay-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="tw:opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="tw:opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
            </svg>
            Загрузка текста…
          </div>
          <template v-else>
            <div v-for="p in fullText" :key="p.page_number" class="tw:mb-5">
              <div class="tw:flex tw:items-center tw:gap-2 tw:mb-1">
                <p class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide">Страница {{ p.page_number }}</p>
              </div>
              <p v-if="p.text" class="tw:text-sm tw:text-ink-800 tw:leading-relaxed tw:whitespace-pre-wrap">{{ p.text }}</p>
              <p v-else class="tw:text-sm tw:text-gray-300">— расшифровка отсутствует —</p>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
