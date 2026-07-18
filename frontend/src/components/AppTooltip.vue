<script setup>
import { ref } from 'vue'

const visible = ref(false)
const triggerRef = ref(null)
const position = ref({ left: '0px', top: '0px' })

function show() {
  const rect = triggerRef.value.getBoundingClientRect()
  position.value = { left: `${rect.left + rect.width / 2}px`, top: `${rect.top}px` }
  visible.value = true
}

function hide() {
  visible.value = false
}
</script>

<template>
  <div
    ref="triggerRef"
    class="tw:inline-block"
    @mouseenter="show"
    @mouseleave="hide"
    @focusin="show"
    @focusout="hide"
  >
    <slot />
    <Teleport to="body">
      <div
        v-if="visible"
        class="tw:fixed tw:z-30 tw:-translate-x-1/2 tw:-translate-y-full tw:-mt-2 tw:px-3 tw:py-2 tw:rounded-lg tw:bg-ink-900 tw:text-white tw:text-xs tw:leading-relaxed tw:shadow-lg tw:whitespace-nowrap tw:pointer-events-none"
        :style="position"
      >
        <slot name="content" />
      </div>
    </Teleport>
  </div>
</template>
