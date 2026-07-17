<script setup>
import { ref } from 'vue'

const visible = ref(false)
</script>

<template>
  <div
    class="tw:relative tw:inline-block"
    @mouseenter="visible = true"
    @mouseleave="visible = false"
    @focusin="visible = true"
    @focusout="visible = false"
  >
    <slot />
    <div
      v-if="visible"
      class="tw:absolute tw:bottom-full tw:left-1/2 tw:-translate-x-1/2 tw:mb-2 tw:z-30 tw:px-3 tw:py-2 tw:rounded-lg tw:bg-ink-900 tw:text-white tw:text-xs tw:leading-relaxed tw:shadow-lg tw:whitespace-nowrap"
    >
      <slot name="content" />
    </div>
  </div>
</template>
