<template>
  <v-card>
    <v-card-title class="text-subtitle-1">Просмотр изменений</v-card-title>
    <v-card-text>
      <v-alert v-if="error" type="error" density="compact">{{ error }}</v-alert>
      <v-alert v-else-if="!loading && !changedRows.length" type="info" density="compact">
        Изменений нет
      </v-alert>
      <div v-else class="d-flex">
        <div class="changes-list">
          <div
            v-for="row in changedRows"
            :key="row.oldPos + '-' + row.newPos + '-' + row.status"
            :id="'change-item-' + row.oldPos + '-' + row.newPos + '-' + row.status"
            class="changes-list-item"
            :class="['bg-' + STATUS_COLORS[row.status] + '-lighten-4', { 'changes-list-item--active': row === selectedRow }]"
            @click="selectedRow = row"
          >
            <img :src="previewUrl(row)" class="changes-list-item-img">
            <v-chip :color="STATUS_COLORS[row.status]" label class="changes-list-item-chip">
              {{ row.oldPos ?? '—' }}/{{ row.newPos ?? '—' }}
            </v-chip>
          </div>
        </div>

        <div class="flex-grow-1 ml-3">
          <template v-if="selectedRow">
            <v-chip :color="STATUS_COLORS[selectedRow.status]" size="small" label class="mb-2">
              {{ STATUS_LABELS[selectedRow.status] }} ({{ selectedRow.oldPos ?? '—' }}/{{ selectedRow.newPos ?? '—' }})
            </v-chip>

            <div class="change-viewer-body">
              <v-btn
                icon="mdi-chevron-left"
                variant="tonal"
                class="change-viewer-arrow change-viewer-arrow--left"
                :disabled="!hasPrev"
                @click="prevItem"
              ></v-btn>
              <v-btn
                icon="mdi-chevron-right"
                variant="tonal"
                class="change-viewer-arrow change-viewer-arrow--right"
                :disabled="!hasNext"
                @click="nextItem"
              ></v-btn>

              <v-row dense>
                <v-col cols="12" :md="showTextColumn ? 7 : 12">
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
                    ></div>
                  </div>
                </v-col>
                <v-col v-if="showTextColumn" cols="12" md="5">
                  <v-progress-circular v-if="textLoading" indeterminate size="20"></v-progress-circular>
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
                </v-col>
              </v-row>
            </div>
          </template>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { diffArrays } from 'diff'
import http from '../../api/http'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
  initialCommit: { type: String, default: null },
  lastCommit: { type: String, default: null },
})

const STATUS_LABELS = {
  removed: 'Удалено',
  new: 'Новое',
  unchanged: 'Без изменений',
  text_changed: 'Текст изменён',
  image_changed: 'Изображение изменено',
  moved: 'Перемещено',
}
const STATUS_COLORS = {
  removed: 'red',
  new: 'green',
  unchanged: 'grey',
  text_changed: 'amber',
  image_changed: 'orange',
  moved: 'blue',
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

// Сколько раз встречается каждое значение поля - используется, чтобы не
// матчить страницы по хешу, который не уникален (см. buildMatcher).
const buildCounts = (pages, field) => {
  const counts = new Map()
  for (const page of pages) {
    const value = page[field]
    if (value == null) continue
    counts.set(value, (counts.get(value) || 0) + 1)
  }
  return counts
}

/*
 * Страница считается "той же" страницей на старой (initial_commit) и новой
 * (last_commit) стороне ветки, если совпадает image_hash ИЛИ text_hash
 * (непустой) - этого требует случай "картинка заменена, текст сохранён"
 * наравне со случаем "текст заменён, картинка сохранена".
 *
 * Хеш засчитывается как совпадение, только если он уникален и в старом, и в
 * новом списке страниц. Иначе, например, все страницы с "убранным" текстом
 * (text_hash - это хеш одного и того же пустого содержимого у всех, см.
 * reset_text) ложно матчились бы друг с другом, из-за чего перемещение
 * страницы могло определиться неверно (сматчить не ту пару, а настоящую
 * пару страниц оставить как "Новое"/"Изображение изменено").
 *
 * diffArrays с этим компаратором сразу даёт выравнивание oldPos <-> newPos:
 * страницы вне пары - добавлены/удалены целиком (вместе с текстом, см.
 * regenerate_branch_cache), для пар остаётся сравнить image_hash и text_hash
 * между собой, чтобы понять, что именно изменилось.
 *
 * Если различаются оба хеша сразу (или оба неуникальны), компаратор их не
 * сматчит - такая пара не отличима от удаления одной страницы и добавления
 * другой, и корректно попадёт в removed+new, а не в один "изменённый" ряд.
 */
const buildMatcher = (oldPages, newPages) => {
  const oldImageCounts = buildCounts(oldPages, 'image_hash')
  const newImageCounts = buildCounts(newPages, 'image_hash')
  const oldTextCounts = buildCounts(oldPages, 'text_hash')
  const newTextCounts = buildCounts(newPages, 'text_hash')

  return (oldPage, newPage) => {
    if (
      oldPage.image_hash != null &&
      oldPage.image_hash === newPage.image_hash &&
      oldImageCounts.get(oldPage.image_hash) === 1 &&
      newImageCounts.get(newPage.image_hash) === 1
    ) return true

    if (
      oldPage.text_hash != null &&
      oldPage.text_hash === newPage.text_hash &&
      oldTextCounts.get(oldPage.text_hash) === 1 &&
      newTextCounts.get(newPage.text_hash) === 1
    ) return true

    return false
  }
}

const diffRows = computed(() => {
  const oldPages = initialPages.value
  const newPages = currentPages.value
  const pagesMatch = buildMatcher(oldPages, newPages)

  const parts = diffArrays(oldPages, newPages, { comparator: pagesMatch })

  const commonRows = []
  const removedEntries = []
  const addedEntries = []
  let oldPos = 0
  let newPos = 0

  for (const part of parts) {
    for (let i = 0; i < part.value.length; i += 1) {
      if (part.removed) {
        oldPos += 1
        removedEntries.push({ oldPos, page: oldPages[oldPos - 1] })
      } else if (part.added) {
        newPos += 1
        addedEntries.push({ newPos, page: newPages[newPos - 1] })
      } else {
        const oldPage = oldPages[oldPos]
        const newPage = newPages[newPos]
        oldPos += 1
        newPos += 1

        const imageSame = oldPage.image_hash === newPage.image_hash
        const textSame = oldPage.text_hash === newPage.text_hash

        let status
        if (imageSame && textSame) status = 'unchanged'
        else if (imageSame) status = 'text_changed'
        else status = 'image_changed'

        commonRows.push({ oldPos, newPos, status })
      }
    }
  }

  /*
   * diffArrays (LCS) добавляет в общую последовательность только страницы,
   * не нарушающие относительный порядок - настоящее перемещение (страница
   * переставлена мимо своего "естественного" места) он поэтому не находит и
   * отдаёт как отдельные removed+added. Ищем среди этих остатков пары с тем
   * же image_hash/text_hash (тем же pagesMatch, что и выше) и превращаем их
   * в одну строку "Перемещено" - в подавляющем большинстве случаев у
   * страницы уникальный хеш, и пара находится однозначно. Если хеш совпадает
   * у нескольких страниц (редкий случай), какие-то из них могут остаться
   * непарными - это ломает только красивость отображения (лишние
   * добавления/удаления вместо перемещения для части страниц), не сам расчёт.
   */
  const usedAdded = new Set()
  const movedRows = []
  const stillRemoved = []

  for (const removedEntry of removedEntries) {
    const matchIndex = addedEntries.findIndex(
      (addedEntry, idx) => !usedAdded.has(idx) && pagesMatch(removedEntry.page, addedEntry.page)
    )
    if (matchIndex === -1) {
      stillRemoved.push(removedEntry)
    } else {
      usedAdded.add(matchIndex)
      movedRows.push({ oldPos: removedEntry.oldPos, newPos: addedEntries[matchIndex].newPos, status: 'moved' })
    }
  }

  const stillAdded = addedEntries.filter((_, idx) => !usedAdded.has(idx))

  const rows = [
    ...commonRows,
    ...movedRows,
    ...stillRemoved.map((entry) => ({ oldPos: entry.oldPos, newPos: null, status: 'removed' })),
    ...stillAdded.map((entry) => ({ oldPos: null, newPos: entry.newPos, status: 'new' })),
  ]

  // Единый порядок отображения: по новой позиции, для чистых удалений - по старой.
  rows.sort((a, b) => (a.newPos ?? a.oldPos) - (b.newPos ?? b.oldPos))

  return rows
})

const changedRows = computed(() => diffRows.value.filter((row) => row.status !== 'unchanged'))

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
  width: 64px;
  padding: 8px 16px 8px 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.05);
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
  width: 56px;
  padding: 4px;
  border-radius: 4px;
  outline: 2px solid transparent;
  outline-offset: -2px;
  transition: outline-color .15s;
  text-align: center;
  margin-bottom: 10px;
}
.changes-list-item--active {
  outline-color: rgb(var(--v-theme-primary));
}
.changes-list-item-img {
  width: 56px;
  height: 56px;
  object-fit: cover;
  border-radius: 4px;
  display: block;
}
.changes-list-item-chip {
  width: 56px;
  min-width: 56px;
  height: auto;
  margin-top: 4px;
  padding: 3px 0;
  justify-content: center;
  font-size: 13px;
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
