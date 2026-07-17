<template>
  <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
    <h2 class="tw:font-serif tw:font-semibold tw:text-ink-900 tw:mb-4">Просмотр изменений</h2>
    <div v-if="error" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2">{{ error }}</div>
    <div v-else-if="!loading && !changedRows.length" class="tw:text-sm tw:text-blue-700 tw:bg-blue-50 tw:border tw:border-blue-200 tw:rounded-lg tw:px-3 tw:py-2">
      Изменений нет
    </div>
    <div v-else class="tw:flex">
      <div class="changes-list">
        <div
          v-for="row in changedRows"
          :id="'change-item-' + row.oldPos + '-' + row.newPos + '-' + row.status"
          :key="row.oldPos + '-' + row.newPos + '-' + row.status"
          class="changes-list-item"
          :class="['changes-list-item--' + row.status, { 'changes-list-item--active': row === selectedRow }]"
          @click="selectedRow = row"
        >
          <img :src="previewUrl(row)" class="changes-list-item-img">
          <div class="changes-list-item-label">{{ row.oldPos ?? '—' }}/{{ row.newPos ?? '—' }}</div>
        </div>
      </div>

      <div class="tw:flex-1 tw:ml-3">
        <template v-if="selectedRow">
          <span
            class="tw:inline-block tw:px-2 tw:py-0.5 tw:rounded tw:text-xs tw:font-semibold tw:mb-2"
            :class="STATUS_CLASSES[selectedRow.status]"
          >
            {{ STATUS_LABELS[selectedRow.status] }} ({{ selectedRow.oldPos ?? '—' }}/{{ selectedRow.newPos ?? '—' }})
          </span>

          <div class="change-viewer-body">
            <button
              type="button"
              :disabled="!hasPrev"
              class="change-viewer-arrow change-viewer-arrow--left tw:bg-white/90 tw:hover:bg-white tw:shadow tw:rounded-full tw:w-9 tw:h-9 tw:flex tw:items-center tw:justify-center tw:disabled:opacity-30 tw:transition-colors"
              @click="prevItem"
            >
              <i class="mdi mdi-chevron-left tw:text-xl" />
            </button>
            <button
              type="button"
              :disabled="!hasNext"
              class="change-viewer-arrow change-viewer-arrow--right tw:bg-white/90 tw:hover:bg-white tw:shadow tw:rounded-full tw:w-9 tw:h-9 tw:flex tw:items-center tw:justify-center tw:disabled:opacity-30 tw:transition-colors"
              @click="nextItem"
            >
              <i class="mdi mdi-chevron-right tw:text-xl" />
            </button>

            <div class="tw:grid tw:grid-cols-1" :class="showTextColumn ? 'tw:md:grid-cols-12 tw:gap-4' : ''">
              <div :class="showTextColumn ? 'tw:md:col-span-7' : ''">
                <div class="change-view-img-wrap">
                  <img :src="fullUrl(selectedRow)" class="change-view-img">
                  <div
                    v-for="(span, idx) in spans"
                    :key="idx"
                    class="change-view-span-highlight"
                    :class="{ 'change-view-span-highlight--active': hoveredSpanIndex === idx }"
                    :style="spanHighlightStyle(span)"
                    @mouseenter="hoveredSpanIndex = idx"
                    @mouseleave="hoveredSpanIndex = null"
                  />
                </div>
              </div>
              <div v-if="showTextColumn" class="tw:md:col-span-5">
                <div v-if="textLoading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
                <div v-else class="change-view-text">
                  <div
                    v-for="(span, idx) in spans"
                    :key="idx"
                    class="change-view-span"
                    :class="{ 'change-view-span--active': hoveredSpanIndex === idx }"
                    @mouseenter="hoveredSpanIndex = idx"
                    @mouseleave="hoveredSpanIndex = null"
                  >{{ span.text }}</div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { structuralDiff } from '../../../../js-packages/structuralDiff/structuralDiff.js'
import http from '../../api/http'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
  initialCommit: { type: String, default: null },
  lastCommit: { type: String, default: null },
})

const STATUS_LABELS = {
  removed: 'Удалено',
  new: 'Новое',
  text_changed: 'Текст изменён',
}
const STATUS_CLASSES = {
  removed: 'tw:bg-red-100 tw:text-red-700',
  new: 'tw:bg-green-100 tw:text-green-700',
  text_changed: 'tw:bg-blue-100 tw:text-blue-700',
}

const currentPages = ref([])
const initialPages = ref([])
const loading = ref(false)
const error = ref('')
const selectedRow = ref(null)
const spans = ref([])
const textLoading = ref(false)
const hoveredSpanIndex = ref(null)

const spanHighlightStyle = (span) => ({
  left: span.rect.x + '%',
  top: span.rect.y + '%',
  width: span.rect.width + '%',
  height: span.rect.height + '%',
})

const loadPagesHash = async (commit) => {
  const response = await http.get(`/api/documents/branches/${props.branchId}/pages_hash`, {
    params: { commit },
  })
  return response.data
}

const load = async () => {
  if (!props.branchId || !props.initialCommit || !props.lastCommit) return

  loading.value = true
  error.value = ''
  try {
    const [currentResult, initialResult] = await Promise.all([
      loadPagesHash(props.lastCommit),
      loadPagesHash(props.initialCommit),
    ])
    currentPages.value = currentResult
    initialPages.value = initialResult
  } catch (err) {
    error.value = 'Не удалось загрузить хеши страниц.'
    console.error('Ошибка при получении хешей страниц:', err)
  } finally {
    loading.value = false
  }
}

watch(() => [props.branchId, props.initialCommit, props.lastCommit], load, { immediate: true })

// Статусы structuralDiff (added/deleted/modified) -> статусы отображения.
const DIFF_STATUS_MAP = {
  added: 'new',
  deleted: 'removed',
  modified: 'text_changed',
}

// structuralDiff сопоставляет страницы по x (image_hash - identity страницы)
// и сравнивает y (text_hash) у сопоставленной пары, чтобы понять, изменился
// ли текст. Если у страницы поменялась картинка (другой image_hash), это уже
// не та же страница - она проходит как удаление старой и добавление новой.
const diffRows = computed(() => {
  const toEntry = (page) => ({ x: page.image_hash ?? '', y: page.text_hash ?? '' })
  const oldArr = initialPages.value.map(toEntry)
  const newArr = currentPages.value.map(toEntry)

  return structuralDiff(oldArr, newArr).map((entry) => ({
    oldPos: entry.oldIndex != null ? entry.oldIndex + 1 : null,
    newPos: entry.newIndex != null ? entry.newIndex + 1 : null,
    status: DIFF_STATUS_MAP[entry.status],
  }))
})

const changedRows = diffRows

// Удалённая страница есть только в initial_commit, во всех остальных случаях смотрим last_commit.
const commitForRow = (row) => (row.status === 'removed' ? props.initialCommit : props.lastCommit)
const posForRow = (row) => (row.status === 'removed' ? row.oldPos : row.newPos)

const previewUrl = (row) => `/api/documents/branches/${props.branchId}/pages/${posForRow(row)}/image/preview?commit=${commitForRow(row)}`
const fullUrl = (row) => `/api/documents/branches/${props.branchId}/pages/${posForRow(row)}/image?commit=${commitForRow(row)}`

const showTextColumn = computed(() => textLoading.value || spans.value.length > 0)

const loadText = async (row) => {
  spans.value = []
  hoveredSpanIndex.value = null
  if (!row) return

  textLoading.value = true
  try {
    const response = await http.get(`/api/documents/branches/${props.branchId}/pages/${posForRow(row)}/text`, {
      params: { commit: commitForRow(row) },
    })
    const page = response.data.text
    if (page && page.blocks) {
      spans.value = page.blocks
    }
  } catch (err) {
    console.error('Ошибка при получении текста страницы:', err)
  } finally {
    textLoading.value = false
  }
}

watch(selectedRow, (row) => {
  loadText(row)
  if (!row) return
  nextTick(() => {
    const id = `change-item-${row.oldPos}-${row.newPos}-${row.status}`
    const el = window.document.getElementById(id)
    if (el) el.scrollIntoView({ inline: 'nearest', block: 'nearest' })
  })
})

watch(changedRows, (rows) => {
  if (!rows.includes(selectedRow.value)) {
    selectedRow.value = rows[0] || null
  }
})

const selectedIndex = computed(() => changedRows.value.indexOf(selectedRow.value))
const hasPrev = computed(() => selectedIndex.value > 0)
const hasNext = computed(() => selectedIndex.value >= 0 && selectedIndex.value < changedRows.value.length - 1)

const prevItem = () => {
  if (hasPrev.value) selectedRow.value = changedRows.value[selectedIndex.value - 1]
}

const nextItem = () => {
  if (hasNext.value) selectedRow.value = changedRows.value[selectedIndex.value + 1]
}

const isTypingTarget = (target) => ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable

const handleKeydown = (event) => {
  if (isTypingTarget(event.target)) return
  if (event.key === 'ArrowLeft') prevItem()
  else if (event.key === 'ArrowRight') nextItem()
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))
</script>

<style scoped>
.changes-list {
  flex: 0 0 auto;
  box-sizing: content-box;
  width: 50px;
  padding: 8px 10px 8px 6px;
  background-color: rgba(0, 0, 0, 0.04);
  border-radius: 6px;
  max-height: 600px;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(128, 128, 128, 0.3) transparent;
}
.changes-list::-webkit-scrollbar {
  width: 3px;
}
.changes-list::-webkit-scrollbar-track {
  background: transparent;
}
.changes-list::-webkit-scrollbar-thumb {
  background-color: rgba(128, 128, 128, 0.3);
  border-radius: 2px;
}
.changes-list-item {
  cursor: pointer;
  box-sizing: content-box;
  width: 37px;
  padding: 3px;
  border-radius: 4px;
  outline: 2px solid transparent;
  outline-offset: -2px;
  transition: outline-color .15s, background-color .15s;
  text-align: center;
  margin-bottom: 8px;
}
.changes-list-item--new {
  background-color: rgba(76, 175, 80, 0.3);
}
.changes-list-item--removed {
  background-color: rgba(244, 67, 54, 0.3);
}
.changes-list-item--text_changed {
  background-color: rgba(33, 150, 243, 0.3);
}
.changes-list-item--active {
  outline-color: var(--tw-color-clay-500, #dc2626);
}
.changes-list-item-img {
  width: 37px;
  height: 37px;
  object-fit: cover;
  border-radius: 4px;
  display: block;
}
.changes-list-item-label {
  font-size: 10px;
  line-height: 1.5;
  font-weight: 600;
}
.change-viewer-body {
  position: relative;
}
.change-viewer-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
}
.change-viewer-arrow--left {
  left: 4px;
}
.change-viewer-arrow--right {
  right: 4px;
}
.change-view-img-wrap {
  position: relative;
  display: inline-block;
  max-width: 100%;
  line-height: 0;
}
.change-view-img {
  max-width: 100%;
  max-height: 75vh;
  display: block;
}
.change-view-span-highlight {
  position: absolute;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  border-radius: 2px;
  transition: background-color .1s, border-color .1s;
}
.change-view-span-highlight--active {
  background: rgba(255, 213, 0, 0.35);
  border-color: rgba(255, 152, 0, 0.9);
}
.change-view-text {
  max-height: 75vh;
  overflow-y: auto;
  line-height: 1.5;
}
.change-view-span {
  display: block;
  cursor: default;
  padding: 3px 4px;
  margin-bottom: 2px;
  border-radius: 2px;
  white-space: pre-line;
}
.change-view-span--active {
  background: rgba(255, 213, 0, 0.35);
}
</style>
