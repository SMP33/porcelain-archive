<template>
  <v-dialog v-model="dialog" max-width="1400">
    <v-card>
      <v-card-text class="pa-2">
        <div class="gallery-viewer-body">
          <v-btn
            icon="mdi-chevron-left"
            variant="tonal"
            class="gallery-viewer-arrow gallery-viewer-arrow--left"
            :disabled="!hasPrev"
            @click="prevPage"
          ></v-btn>
          <v-btn
            icon="mdi-chevron-right"
            variant="tonal"
            class="gallery-viewer-arrow gallery-viewer-arrow--right"
            :disabled="!hasNext"
            @click="nextPage"
          ></v-btn>

          <v-row dense>
            <v-col cols="12" :md="showTextColumn ? 7 : 12">
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
                ></div>
              </div>
            </v-col>
            <v-col v-if="showTextColumn" cols="12" md="5">
              <v-progress-circular v-if="textLoading" indeterminate size="20"></v-progress-circular>
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
            </v-col>
          </v-row>
        </div>

        <div class="page-thumb-strip">
          <div
            v-for="pos in pageCount"
            :key="pos"
            :id="'gallery-thumb-' + pos"
            class="page-thumb-strip-item"
            :class="{ 'page-thumb-strip-item--active': pos === currentPos }"
            @click="show(pos)"
          >
            <img :src="previewImageUrl(pos)" class="page-thumb-strip-img">
            <div class="page-thumb-strip-label">{{ pos }}</div>
          </div>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-btn
          icon="mdi-chevron-left"
          variant="text"
          :disabled="!hasPrev"
          @click="prevPage"
        ></v-btn>
        <span class="text-caption">Страница {{ currentPos }} из {{ pageCount }}</span>
        <v-btn
          icon="mdi-chevron-right"
          variant="text"
          :disabled="!hasNext"
          @click="nextPage"
        ></v-btn>
        <v-spacer></v-spacer>
        <v-btn @click="dialog = false">Закрыть</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, nextTick, watch, onUnmounted } from 'vue'
import http from '../api/http'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
  pageCount: { type: Number, required: true },
})

const dialog = ref(false)
const dialogUrl = ref('')
const currentPos = ref(1)
const spans = ref([])
const textLoading = ref(false)
const hoveredSpanIndex = ref(null)

const hasPrev = computed(() => currentPos.value > 1)
const hasNext = computed(() => currentPos.value < props.pageCount)
const showTextColumn = computed(() => textLoading.value || spans.value.length > 0)

const previewImageUrl = (pos) => `/api/documents/branches/${props.branchId}/pages/${pos}/image/preview`
const fullImageUrl = (pos) => `/api/documents/branches/${props.branchId}/pages/${pos}/image`

const spanHighlightStyle = (span) => ({
  left: span.rect.x + '%',
  top: span.rect.y + '%',
  width: span.rect.width + '%',
  height: span.rect.height + '%',
})

const loadText = async (pos) => {
  spans.value = []
  hoveredSpanIndex.value = null
  textLoading.value = true
  try {
    const response = await http.get(`/api/documents/branches/${props.branchId}/pages/${pos}/text`)
    const page = response.data.text
    if (page && page.blocks) {
      spans.value = page.blocks
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
  outline-color: rgb(var(--v-theme-primary));
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
