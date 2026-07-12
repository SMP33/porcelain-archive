<template>
  <v-text-field
    :model-value="modelValue"
    @update:model-value="onUpdate"
    :label="label"
    type="number"
    density="compact"
    :min="min"
    :max="max"
    class="page-number-field"
    @wheel="onWheel"
    @focus="focused = true"
    @blur="focused = false"
  ></v-text-field>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  label: { type: String, default: '' },
  min: { type: [Number, String], default: undefined },
  max: { type: [Number, String], default: undefined },
})

const emit = defineEmits(['update:modelValue'])

const focused = ref(false)

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
.page-number-field :deep(input[type="number"]) {
  -moz-appearance: textfield;
}
.page-number-field :deep(input[type="number"]::-webkit-inner-spin-button),
.page-number-field :deep(input[type="number"]::-webkit-outer-spin-button) {
  -webkit-appearance: none;
  margin: 0;
}
</style>
