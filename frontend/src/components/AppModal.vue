<script setup>
import { watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  maxWidth: { type: String, default: 'tw:max-w-md' },
  bodyClass: { type: String, default: 'tw:p-6' },
  persistent: { type: Boolean, default: false },
  showClose: { type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}

function onBackdropClick() {
  if (!props.persistent) close()
}

function onKeydown(e) {
  if (e.key === 'Escape') close()
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      document.addEventListener('keydown', onKeydown)
      document.body.style.overflow = 'hidden'
    } else {
      document.removeEventListener('keydown', onKeydown)
      document.body.style.overflow = ''
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue" class="tw:fixed tw:inset-0 tw:z-50 tw:flex tw:items-center tw:justify-center tw:p-4">
      <div class="tw:absolute tw:inset-0 tw:bg-black/50" @click="onBackdropClick" />
      <div
        class="tw:relative tw:bg-white tw:rounded-xl tw:shadow-lg tw:w-full tw:max-h-[90vh] tw:overflow-y-auto tw:flex tw:flex-col"
        :class="maxWidth"
      >
        <button
          v-if="showClose"
          type="button"
          class="tw:absolute tw:top-3 tw:right-3 tw:text-gray-400 tw:hover:text-gray-600 tw:transition-colors tw:z-10"
          @click="close"
        >
          <i class="mdi mdi-close tw:text-xl" />
        </button>
        <div :class="bodyClass">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>
