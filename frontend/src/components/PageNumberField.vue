<template>
  <div>
    <label v-if="label" class="tw:block tw:text-xs tw:font-medium tw:text-gray-600 tw:mb-1">{{ label }}</label>
    <input
      :value="modelValue"
      type="number"
      :min="min"
      :max="max"
      class="page-number-field tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-1.5 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"
      @input="onUpdate($event.target.value)"
      @wheel="onWheel"
      @focus="handleFocus"
      @blur="focused = false"
    >
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  label: { type: String, default: '' },
  min: { type: [Number, String], default: undefined },
  max: { type: [Number, String], default: undefined },
})

const emit = defineEmits(['update:modelValue', 'focus'])

const focused = ref(false)

const handleFocus = () => {
  focused.value = true
  emit('focus')
}

const onUpdate = (val) => {
  emit('update:modelValue', val === '' ? '' : Number(val))
}

// Прокрутка колесом меняет значение на 1, только пока поле в фокусе -
// иначе скролл страницы через число ломался бы при простой прокрутке мимо.
const onWheel = (event) => {
  if (!focused.value) return
  event.preventDefault()

  const step = event.deltaY < 0 ? 1 : -1
  let current = Number(props.modelValue)
  if (Number.isNaN(current)) current = 0
  let next = current + step

  if (props.min !== undefined && next < Number(props.min)) next = Number(props.min)
  if (props.max !== undefined && next > Number(props.max)) next = Number(props.max)

  emit('update:modelValue', next)
}
</script>

<style scoped>
.page-number-field {
  -moz-appearance: textfield;
}
.page-number-field::-webkit-inner-spin-button,
.page-number-field::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
</style>
