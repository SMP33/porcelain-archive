<template>
  <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
    <h2 class="tw:font-serif tw:font-semibold tw:text-ink-900 tw:mb-4">Распознать текст</h2>
    <div class="tw:grid tw:grid-cols-2 tw:gap-3">
      <PageNumberField
        v-model="recognizeStart"
        label="Со страницы"
        :min="1"
        :max="pageCount"
        @focus="focusedField = 'start'"
      />
      <PageNumberField
        v-model="recognizeEnd"
        label="По страницу"
        :min="recognizeStart || 1"
        :max="pageCount"
        @focus="focusedField = 'end'"
      />
    </div>
    <div v-if="recognizeError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      {{ recognizeError }}
    </div>
    <div v-if="recognizeSuccess" class="tw:text-sm tw:text-green-700 tw:bg-green-50 tw:border tw:border-green-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      Задача на распознавание текста поставлена в очередь.
    </div>
    <button
      type="button"
      :disabled="!canRecognizeText || recognizingText"
      class="tw:mt-4 tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
      @click="handleRecognizeText"
    >
      {{ recognizingText ? 'Отправка…' : 'Распознать текст' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import http from '../../api/http'
import PageNumberField from '../PageNumberField.vue'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
  pageCount: { type: Number, required: true },
})

const emit = defineEmits(['submitted'])

const recognizeStart = ref(null)
const recognizeEnd = ref(null)
const recognizingText = ref(false)
const recognizeError = ref('')
const recognizeSuccess = ref(false)
const focusedField = ref(null)

const canRecognizeText = computed(() => {
  if (!props.pageCount) return false
  const start = recognizeStart.value
  const end = recognizeEnd.value
  if (!Number.isInteger(start) || !Number.isInteger(end)) return false
  return start >= 1 && end >= start && end <= props.pageCount
})

// Диапазон распознаваемых страниц - используется EditView для подсветки плиток.
// Подсвечивается сразу по мере ввода, не дожидаясь заполнения обоих полей -
// незаполненное поле считается равным заполненному.
const highlightRange = computed(() => {
  const start = Number.isInteger(recognizeStart.value) ? recognizeStart.value : null
  const end = Number.isInteger(recognizeEnd.value) ? recognizeEnd.value : null
  if (start == null && end == null) return null
  const rangeStart = start ?? end
  const rangeEnd = end ?? start
  return { start: Math.min(rangeStart, rangeEnd), end: Math.max(rangeStart, rangeEnd) }
})

// Страница, которую нужно показать в области плиток - зависит от того, какое
// поле сейчас в фокусе (начало или конец диапазона).
const scrollTargetPos = computed(() => {
  const pos = focusedField.value === 'start' ? recognizeStart.value : focusedField.value === 'end' ? recognizeEnd.value : null
  return Number.isInteger(pos) ? pos : null
})

defineExpose({ highlightRange, scrollTargetPos })

const handleRecognizeText = async () => {
  recognizingText.value = true
  recognizeError.value = ''
  recognizeSuccess.value = false
  try {
    await http.post(`/api/documents/branches/${props.branchId}/text/recognize`, {
      start: recognizeStart.value,
      end: recognizeEnd.value,
    })
    recognizeSuccess.value = true
    emit('submitted')
  } catch (err) {
    recognizeError.value = 'Не удалось поставить задачу в очередь.'
    console.error('Ошибка при распознавании текста:', err)
  } finally {
    recognizingText.value = false
  }
}
</script>
