<template>
  <div>
    <div v-if="spans.length" class="tw:flex tw:items-center tw:gap-1 tw:mb-2">
      <button
        type="button"
        class="tw:px-2 tw:py-1 tw:text-xs tw:rounded tw:transition-colors"
        :class="mode === 'list' ? 'tw:bg-clay-100 tw:text-clay-700' : 'tw:text-gray-500 tw:hover:bg-gray-50'"
        @click="mode = 'list'"
      >
        Списком
      </button>
      <button
        type="button"
        class="tw:px-2 tw:py-1 tw:text-xs tw:rounded tw:transition-colors"
        :class="mode === 'layout' ? 'tw:bg-clay-100 tw:text-clay-700' : 'tw:text-gray-500 tw:hover:bg-gray-50'"
        @click="mode = 'layout'"
      >
        Как на странице
      </button>
    </div>
    <div v-if="textLoading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
    <div
      v-else-if="mode === 'layout'"
      ref="layoutCanvasRef"
      class="page-layout-canvas"
      :style="{ aspectRatio: pageSize.width && pageSize.height ? `${pageSize.width} / ${pageSize.height}` : undefined }"
    >
      <div
        v-for="(span, idx) in spans"
        :key="idx"
        :ref="(el) => setLayoutBlockEl(el, idx)"
        class="page-layout-block"
        :class="{ 'page-layout-block--active': hoveredIndex === idx }"
        :style="layoutBlockStyle(span)"
        @mouseenter="$emit('update:hoveredIndex', idx)"
        @mouseleave="$emit('update:hoveredIndex', null)"
      >{{ span.text }}</div>
    </div>
    <div v-else class="page-text-panel">
      <div
        v-for="(span, idx) in spans"
        :key="idx"
        class="page-text-span"
        :class="{ 'page-text-span--active': hoveredIndex === idx }"
        @mouseenter="$emit('update:hoveredIndex', idx)"
        @mouseleave="$emit('update:hoveredIndex', null)"
      >{{ span.text }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onUnmounted } from 'vue'

const props = defineProps({
  spans: { type: Array, default: () => [] },
  pageSize: { type: Object, default: () => ({ width: 0, height: 0 }) },
  textLoading: { type: Boolean, default: false },
  hoveredIndex: { default: null },
})

defineEmits(['update:hoveredIndex'])

const MIN_LAYOUT_FONT_PX = 9
const MAX_LAYOUT_FONT_PX = 200

const mode = ref('list')
const layoutCanvasRef = ref(null)
const layoutBlockEls = ref([])

// Позиция, размер и выравнивание блока в режиме "как на странице" - размер шрифта
// сюда не входит, он подбирается отдельно (см. fitLayoutBlockFont) под фактические
// пиксели блока, а не проставляется через :style, чтобы не перетираться при ререндере.
const layoutBlockStyle = (span) => ({
  left: span.rect.x + '%',
  top: span.rect.y + '%',
  width: span.rect.width + '%',
  height: span.rect.height + '%',
  textAlign: span.alignment || 'left',
})

const setLayoutBlockEl = (el, idx) => {
  layoutBlockEls.value[idx] = el || null
}

const layoutBlockFits = (el) => (
  el.scrollHeight <= el.clientHeight + 0.5 && el.scrollWidth <= el.clientWidth + 0.5
)

// Подбирает максимальный размер шрифта, при котором текст блока помещается в его
// рамку (без обрезки), но не меньше MIN_LAYOUT_FONT_PX. Если текст не помещается
// даже при минимальном размере, оставляет минимальный и не обрезает его (overflow: visible) -
// лучше вылезти за рамку блока, чем сделать нечитаемо мелкий шрифт или обрезать текст.
const fitLayoutBlockFont = (el) => {
  if (!el || !el.clientHeight || !el.clientWidth) return
  el.style.overflow = 'hidden'
  el.style.fontSize = `${MIN_LAYOUT_FONT_PX}px`
  if (!layoutBlockFits(el)) {
    el.style.overflow = 'visible'
    return
  }
  let lo = MIN_LAYOUT_FONT_PX
  let hi = MAX_LAYOUT_FONT_PX
  while (hi - lo > 1) {
    const mid = Math.floor((lo + hi) / 2)
    el.style.fontSize = `${mid}px`
    if (layoutBlockFits(el)) lo = mid
    else hi = mid
  }
  el.style.fontSize = `${lo}px`
}

const refitLayoutBlocks = () => {
  nextTick(() => {
    layoutBlockEls.value.forEach((el) => fitLayoutBlockFont(el))
  })
}

watch([mode, () => props.spans], () => {
  if (mode.value === 'layout') {
    refitLayoutBlocks()
  }
})

let layoutResizeObserver = null
watch(layoutCanvasRef, (el) => {
  layoutResizeObserver?.disconnect()
  if (el) {
    layoutResizeObserver = new ResizeObserver(() => refitLayoutBlocks())
    layoutResizeObserver.observe(el)
  }
})

onUnmounted(() => {
  layoutResizeObserver?.disconnect()
})
</script>

<style scoped>
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
.page-layout-canvas {
  position: relative;
  width: 100%;
  max-height: 75vh;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  overflow-x: hidden;
  overflow-y: auto;
}
.page-layout-block {
  position: absolute;
  overflow: hidden;
  line-height: 1.15;
  white-space: pre-wrap;
  overflow-wrap: break-word;
  padding: 1px 2px;
  cursor: default;
  border-radius: 2px;
  transition: background-color .1s;
}
.page-layout-block--active {
  background: rgba(255, 213, 0, 0.35);
}
</style>
