<template>
  <AppModal v-model="dialog" max-width="tw:max-w-[1400px]" body-class="tw:p-4">
    <div class="gallery-viewer-body">
      <button
        type="button"
        :disabled="!hasPrev"
        class="gallery-viewer-arrow gallery-viewer-arrow--left tw:bg-white/90 tw:hover:bg-white tw:shadow tw:rounded-full tw:w-9 tw:h-9 tw:flex tw:items-center tw:justify-center tw:disabled:opacity-30 tw:disabled:cursor-not-allowed tw:transition-colors"
        @click="prevPage"
      >
        <i class="mdi mdi-chevron-left tw:text-xl" />
      </button>
      <button
        type="button"
        :disabled="!hasNext"
        class="gallery-viewer-arrow gallery-viewer-arrow--right tw:bg-white/90 tw:hover:bg-white tw:shadow tw:rounded-full tw:w-9 tw:h-9 tw:flex tw:items-center tw:justify-center tw:disabled:opacity-30 tw:disabled:cursor-not-allowed tw:transition-colors"
        @click="nextPage"
      >
        <i class="mdi mdi-chevron-right tw:text-xl" />
      </button>

      <div v-if="pageOcrQuality" class="tw:mb-2">
        <span
          class="tw:inline-flex tw:items-center tw:gap-1 tw:px-2 tw:py-0.5 tw:rounded-full tw:text-xs tw:font-medium"
          :class="ocrQualityBadgeClass"
        >
          Качество распознавания: {{ ocrQualityLabel }}
        </span>
      </div>

      <div class="tw:grid tw:grid-cols-1" :class="showTextColumn ? 'tw:md:grid-cols-12 tw:gap-4' : ''">
        <div :class="showTextColumn ? 'tw:md:col-span-7' : ''">
          <div class="page-image-wrap">
            <img :src="dialogUrl">
            <div
              v-for="(span, idx) in spans"
              :key="idx"
              class="page-span-highlight"
              :class="{ 'page-span-highlight--active': hoveredSpanIndex === idx }"
              :style="spanHighlightStyle(span)"
              @mouseenter="hoveredSpanIndex = idx"
              @mouseleave="hoveredSpanIndex = null"
            />
          </div>
        </div>
        <div v-if="showTextColumn" class="tw:md:col-span-5">
          <div v-if="textLoading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
          <div v-else class="page-text-panel">
            <div
              v-for="(span, idx) in spans"
              :key="idx"
              class="page-text-span"
              :class="{ 'page-text-span--active': hoveredSpanIndex === idx }"
              @mouseenter="hoveredSpanIndex = idx"
              @mouseleave="hoveredSpanIndex = null"
            >{{ span.text }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="page-thumb-strip" @wheel="onThumbStripWheel">
      <div
        v-for="pos in pageCount"
        :id="'gallery-thumb-' + pos"
        :key="pos"
        class="page-thumb-strip-item"
        :class="{ 'page-thumb-strip-item--active': pos === currentPos }"
        @click="show(pos)"
      >
        <img :src="previewImageUrl(pos)" class="page-thumb-strip-img">
        <div class="page-thumb-strip-label tw:text-gray-500">{{ pos }}</div>
      </div>
    </div>

    <div class="tw:flex tw:items-center tw:gap-2 tw:mt-2 tw:pt-2 tw:border-t tw:border-gray-100">
      <button type="button" :disabled="!hasPrev" class="tw:p-2 tw:text-gray-500 tw:hover:text-clay-500 tw:disabled:opacity-30 tw:transition-colors" @click="prevPage">
        <i class="mdi mdi-chevron-left tw:text-lg" />
      </button>
      <span class="tw:text-xs tw:text-gray-500">Страница {{ currentPos }} из {{ pageCount }}</span>
      <button type="button" :disabled="!hasNext" class="tw:p-2 tw:text-gray-500 tw:hover:text-clay-500 tw:disabled:opacity-30 tw:transition-colors" @click="nextPage">
        <i class="mdi mdi-chevron-right tw:text-lg" />
      </button>
      <div class="tw:flex-1" />
      <button type="button" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors" @click="dialog = false">Закрыть</button>
    </div>
  </AppModal>
</template>

<script setup>
import { ref, computed, nextTick, watch, onUnmounted } from 'vue'
import http from '../api/http'
import AppModal from './AppModal.vue'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
  pageCount: { type: Number, required: true },
  commit: { type: String, default: null },
})

const dialog = ref(false)
const dialogUrl = ref('')
const currentPos = ref(1)
const spans = ref([])
const textLoading = ref(false)
const hoveredSpanIndex = ref(null)
const pageOcrQuality = ref(null)

const hasPrev = computed(() => currentPos.value > 1)
const hasNext = computed(() => currentPos.value < props.pageCount)
const showTextColumn = computed(() => textLoading.value || spans.value.length > 0)

const OCR_QUALITY_LABELS = { high: 'Высокое', low: 'Низкое', worst: 'Очень низкое' }
const ocrQualityLabel = computed(() => OCR_QUALITY_LABELS[pageOcrQuality.value] || pageOcrQuality.value)
const OCR_QUALITY_BADGE_CLASSES = {
  high: 'tw:bg-green-100 tw:text-green-700',
  low: 'tw:bg-yellow-100 tw:text-yellow-800',
  worst: 'tw:bg-red-100 tw:text-red-700',
}
const ocrQualityBadgeClass = computed(() => OCR_QUALITY_BADGE_CLASSES[pageOcrQuality.value] || 'tw:bg-gray-100 tw:text-gray-700')

// Переводит вертикальную прокрутку колесом мыши в горизонтальную прокрутку ленты миниатюр.
const onThumbStripWheel = (event) => {
  event.preventDefault()
  event.currentTarget.scrollLeft += event.deltaY
}

// commit в query - чтобы браузер не отдавал закешированное изображение
// с прежним содержимым той же позиции после изменения страниц ветки.
const commitQuery = () => (props.commit ? `?commit=${encodeURIComponent(props.commit)}` : '')
const previewImageUrl = (pos) => `/api/documents/branches/${props.branchId}/pages/${pos}/image/preview${commitQuery()}`
const fullImageUrl = (pos) => `/api/documents/branches/${props.branchId}/pages/${pos}/image${commitQuery()}`

const spanHighlightStyle = (span) => ({
  left: span.rect.x + '%',
  top: span.rect.y + '%',
  width: span.rect.width + '%',
  height: span.rect.height + '%',
})

const loadText = async (pos) => {
  spans.value = []
  hoveredSpanIndex.value = null
  pageOcrQuality.value = null
  textLoading.value = true
  try {
    const response = await http.get(`/api/documents/branches/${props.branchId}/pages/${pos}/text`)
    const page = response.data.text
    if (page && page.blocks) {
      spans.value = page.blocks
    }
    if (page && page.ocr_quality) {
      pageOcrQuality.value = page.ocr_quality
    }
  } catch (error) {
    console.error('Ошибка при получении текста страницы:', error)
  } finally {
    textLoading.value = false
  }
}

const show = (pos) => {
  currentPos.value = pos
  dialogUrl.value = fullImageUrl(pos)
  dialog.value = true
  loadText(pos)
  nextTick(() => {
    const el = window.document.getElementById(`gallery-thumb-${pos}`)
    if (el) el.scrollIntoView({ inline: 'nearest', block: 'nearest' })
  })
}

const prevPage = () => {
  if (hasPrev.value) show(currentPos.value - 1)
}

const nextPage = () => {
  if (hasNext.value) show(currentPos.value + 1)
}

const isTypingTarget = (target) => ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable

const handleKeydown = (event) => {
  if (isTypingTarget(event.target)) return
  if (event.key === 'ArrowLeft') prevPage()
  else if (event.key === 'ArrowRight') nextPage()
}

watch(dialog, (isOpen) => {
  if (isOpen) {
    window.addEventListener('keydown', handleKeydown)
  } else {
    window.removeEventListener('keydown', handleKeydown)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

defineExpose({ show, previewImageUrl })
</script>

<style scoped>
.gallery-viewer-body {
  position: relative;
}
.gallery-viewer-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
}
.gallery-viewer-arrow--left {
  left: 4px;
}
.gallery-viewer-arrow--right {
  right: 4px;
}
.page-image-wrap {
  position: relative;
  display: inline-block;
  max-width: 100%;
  line-height: 0;
}
.page-image-wrap img {
  max-width: 100%;
  max-height: 75vh;
  display: block;
}
.page-span-highlight {
  position: absolute;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  border-radius: 2px;
  transition: background-color .1s, border-color .1s;
}
.page-span-highlight--active {
  background: rgba(255, 213, 0, 0.35);
  border-color: rgba(255, 152, 0, 0.9);
}
.page-text-panel {
  max-height: 75vh;
  overflow-y: auto;
  line-height: 1.5;
}
.page-text-span {
  display: block;
  cursor: default;
  padding: 3px 4px;
  margin-bottom: 2px;
  border-radius: 2px;
  white-space: pre-line;
}
.page-text-span--active {
  background: rgba(255, 213, 0, 0.35);
}
.page-thumb-strip {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding: 6px 2px;
}
.page-thumb-strip-item {
  flex: 0 0 auto;
  width: 64px;
  cursor: pointer;
  opacity: 0.55;
  border-radius: 4px;
  outline: 2px solid transparent;
  outline-offset: -2px;
  transition: opacity .15s, outline-color .15s;
  text-align: center;
}
.page-thumb-strip-item--active {
  opacity: 1;
  outline-color: var(--tw-color-clay-500, #dc2626);
}
.page-thumb-strip-img {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 4px;
  display: block;
}
.page-thumb-strip-label {
  font-size: 11px;
  line-height: 1.6;
}
</style>
