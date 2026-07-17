<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: null },
  options: { type: Array, required: true }, // [{ value, title, color }]
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const rootEl = ref(null)

const selected = computed(() => props.options.find((o) => o.value === props.modelValue) || null)

function toggle() {
  if (props.disabled || props.loading) return
  open.value = !open.value
}

function select(option) {
  open.value = false
  if (option.value !== props.modelValue) emit('update:modelValue', option.value)
}

function onDocClick(e) {
  if (rootEl.value && !rootEl.value.contains(e.target)) open.value = false
}

function onKeydown(e) {
  if (e.key === 'Escape') open.value = false
}

watch(open, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', onDocClick, true)
    document.addEventListener('keydown', onKeydown)
  } else {
    document.removeEventListener('click', onDocClick, true)
    document.removeEventListener('keydown', onKeydown)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick, true)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div ref="rootEl" class="tw:relative tw:inline-block">
    <button
      type="button"
      :disabled="disabled || loading"
      class="tw:flex tw:items-center tw:gap-2 tw:px-3 tw:py-1.5 tw:rounded-lg tw:border tw:border-gray-300 tw:text-sm tw:bg-white tw:hover:bg-gray-50 tw:transition-colors tw:disabled:opacity-50 tw:disabled:cursor-not-allowed"
      @click="toggle"
    >
      <i v-if="loading" class="mdi mdi-loading tw:animate-spin tw:text-gray-400" />
      <span v-else-if="selected" :style="{ color: selected.color }">{{ selected.title }}</span>
      <span v-else class="tw:text-gray-400">{{ placeholder }}</span>
      <i class="mdi mdi-chevron-down tw:text-gray-400" />
    </button>
    <div
      v-if="open"
      class="tw:absolute tw:z-20 tw:mt-1 tw:min-w-full tw:bg-white tw:rounded-lg tw:border tw:border-gray-200 tw:shadow-lg tw:py-1 tw:whitespace-nowrap"
    >
      <button
        v-for="opt in options.filter((o) => !o.hidden)"
        :key="opt.value"
        type="button"
        class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-1.5 tw:text-sm tw:hover:bg-gray-50 tw:transition-colors"
        :style="{ color: opt.color }"
        @click="select(opt)"
      >
        {{ opt.title }}
      </button>
    </div>
  </div>
</template>
