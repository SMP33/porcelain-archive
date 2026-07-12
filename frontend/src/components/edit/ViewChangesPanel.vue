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
            :class="{ 'changes-list-item--active': row === selectedRow }"
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
  masterBranchId: { type: [Number, String], default: null },
})

const STATUS_LABELS = {
  removed: 'Удалено',
  new: 'Новое',
  unchanged: 'Без изменений',
  text_changed: 'Текст изменён',
  image_changed: 'Изображение изменено',
}
const STATUS_COLORS = {
  removed: 'red',
  new: 'green',
  unchanged: 'grey',
  text_changed: 'amber',
  image_changed: 'orange',
}

const branchPages = ref([])
const masterPages = ref([])
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

const loadPagesHash = async (id) => {
  const response = await http.get(`/api/documents/branches/${id}/pages_hash`)
  return response.data
}

const load = async () => {
  if (!props.branchId || !props.masterBranchId) return

  loading.value = true
  error.value = ''
  try {
    const [branchResult, masterResult] = await Promise.all([
      loadPagesHash(props.branchId),
      loadPagesHash(props.masterBranchId),
    ])
    branchPages.value = branchResult
    masterPages.value = masterResult
  } catch (err) {
    error.value = 'Не удалось загрузить хеши страниц.'
    console.error('Ошибка при получении хешей страниц:', err)
  } finally {
    loading.value = false
  }
}

watch(() => [props.branchId, props.masterBranchId], load, { immediate: true })

/*
 * Страница считается "той же" страницей на старой (master) и новой (текущая
 * ветка) стороне, если совпадает image_hash ИЛИ text_hash (непустой) -
 * этого требует случай "картинка заменена, текст сохранён" наравне со
 * случаем "текст заменён, картинка сохранена". Пустой/null text_hash не
 * считается совпадением сам по себе - иначе все безтекстовые страницы
 * ложно матчились бы друг с другом.
 *
 * diffArrays с этим компаратором сразу даёт выравнивание oldPos <-> newPos:
 * страницы вне пары - добавлены/удалены целиком (вместе с текстом, см.
 * regenerate_branch_cache), для пар остаётся сравнить image_hash и text_hash
 * между собой, чтобы понять, что именно изменилось.
 *
 * Если различаются оба хеша сразу, компаратор их не сматчит - такая пара
 * не отличима от удаления одной страницы и добавления другой, и корректно
 * попадёт в removed+new, а не в один "изменённый" ряд.
 */
const pagesMatch = (oldPage, newPage) => {
  if (oldPage.image_hash != null && oldPage.image_hash === newPage.image_hash) return true
  if (oldPage.text_hash != null && oldPage.text_hash === newPage.text_hash) return true
  return false
}

const diffRows = computed(() => {
  const oldPages = masterPages.value
  const newPages = branchPages.value

  const parts = diffArrays(oldPages, newPages, { comparator: pagesMatch })

  const rows = []
  let oldPos = 0
  let newPos = 0

  for (const part of parts) {
    for (let i = 0; i < part.value.length; i += 1) {
      if (part.removed) {
        oldPos += 1
        rows.push({ oldPos, newPos: null, status: 'removed' })
      } else if (part.added) {
        newPos += 1
        rows.push({ oldPos: null, newPos, status: 'new' })
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

        rows.push({ oldPos, newPos, status })
      }
    }
  }

  return rows
})

const changedRows = computed(() => diffRows.value.filter((row) => row.status !== 'unchanged'))

// Удалённая страница есть только в master, во всех остальных случаях смотрим текущую ветку.
const branchForRow = (row) => (row.status === 'removed' ? props.masterBranchId : props.branchId)
const posForRow = (row) => (row.status === 'removed' ? row.oldPos : row.newPos)

const previewUrl = (row) => `/api/documents/branches/${branchForRow(row)}/pages/${posForRow(row)}/image/preview`
const fullUrl = (row) => `/api/documents/branches/${branchForRow(row)}/pages/${posForRow(row)}/image`

const showTextColumn = computed(() => textLoading.value || spans.value.length > 0)

const loadText = async (row) => {
  spans.value = []
  hoveredSpanIndex.value = null
  if (!row) return

  textLoading.value = true
  try {
    const response = await http.get(`/api/documents/branches/${branchForRow(row)}/pages/${posForRow(row)}/text`)
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
  width: 56px;
  max-height: 600px;
  overflow-y: auto;
}
.changes-list-item {
  cursor: pointer;
  width: 56px;
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
