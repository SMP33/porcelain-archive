<template>
  <div ref="rootEl" class="tw:flex tw:h-full tw:w-full tw:min-h-0">
    <div :style="{ width: leftWidth + '%' }" class="tw:overflow-auto tw:min-w-0">
      <slot name="left" />
    </div>
    <div
      class="tw:w-1.5 tw:shrink-0 tw:cursor-col-resize tw:bg-gray-200 tw:hover:bg-clay-300 tw:transition-colors"
      @mousedown="startDrag"
    />
    <div class="tw:flex-1 tw:overflow-auto tw:min-w-0">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'

const props = defineProps({
  initialLeftPercent: { type: Number, default: 35 },
})

const rootEl = ref(null)
const leftWidth = ref(props.initialLeftPercent)
let dragging = false

function startDrag(e) {
  dragging = true
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  e.preventDefault()
}

function onDrag(e) {
  if (!dragging || !rootEl.value) return
  const rect = rootEl.value.getBoundingClientRect()
  const pct = ((e.clientX - rect.left) / rect.width) * 100
  leftWidth.value = Math.min(80, Math.max(15, pct))
}

function stopDrag() {
  dragging = false
  document.body.style.userSelect = ''
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

onBeforeUnmount(stopDrag)
</script>
