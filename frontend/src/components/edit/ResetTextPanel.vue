<template>
  <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
    <h2 class="tw:font-serif tw:font-semibold tw:text-ink-900 tw:mb-4">Убрать текст</h2>
    <div class="tw:grid tw:grid-cols-2 tw:gap-3">
      <PageNumberField
        v-model="resetTextStart"
        label="Со страницы"
        :min="1"
        :max="pageCount"
        @focus="focusedField = 'start'"
      />
      <PageNumberField
        v-model="resetTextEnd"
        label="По страницу"
        :min="resetTextStart || 1"
        :max="pageCount"
        @focus="focusedField = 'end'"
      />
    </div>
    <div v-if="resetTextError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      {{ resetTextError }}
    </div>
    <div v-if="resetTextSuccess" class="tw:text-sm tw:text-green-700 tw:bg-green-50 tw:border tw:border-green-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      Задача на удаление текста поставлена в очередь.
    </div>
    <button
      type="button"
      :disabled="!canResetText || resettingText"
      class="tw:mt-4 tw:px-5 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
      @click="handleResetText"
    >
      {{ resettingText ? 'Отправка…' : 'Убрать текст' }}
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

const resetTextStart = ref(null)
const resetTextEnd = ref(null)
const resettingText = ref(false)
const resetTextError = ref('')
const resetTextSuccess = ref(false)
const focusedField = ref(null)

const canResetText = computed(() => {
  if (!props.pageCount) return false
  const start = resetTextStart.value
  const end = resetTextEnd.value
  if (!Number.isInteger(start) || !Number.isInteger(end)) return false
  return start >= 1 && end >= start && end <= props.pageCount
})

// Диапазон страниц, у которых будет убран текст - используется EditView для подсветки плиток.
// Подсвечивается сразу по мере ввода, не дожидаясь заполнения обоих полей -
// незаполненное поле считается равным заполненному.
const highlightRange = computed(() => {
  const start = Number.isInteger(resetTextStart.value) ? resetTextStart.value : null
  const end = Number.isInteger(resetTextEnd.value) ? resetTextEnd.value : null
  if (start == null && end == null) return null
  const rangeStart = start ?? end
  const rangeEnd = end ?? start
  return { start: Math.min(rangeStart, rangeEnd), end: Math.max(rangeStart, rangeEnd) }
})

// Страница, которую нужно показать в области плиток - зависит от того, какое
// поле сейчас в фокусе (начало или конец диапазона).
const scrollTargetPos = computed(() => {
  const pos = focusedField.value === 'start' ? resetTextStart.value : focusedField.value === 'end' ? resetTextEnd.value : null
  return Number.isInteger(pos) ? pos : null
})

defineExpose({ highlightRange, scrollTargetPos })

const handleResetText = async () => {
  resettingText.value = true
  resetTextError.value = ''
  resetTextSuccess.value = false
  try {
    await http.post(`/api/documents/branches/${props.branchId}/text/reset`, {
      start: resetTextStart.value,
      end: resetTextEnd.value,
    })
    resetTextSuccess.value = true
    emit('submitted')
  } catch (err) {
    resetTextError.value = 'Не удалось поставить задачу в очередь.'
    console.error('Ошибка при удалении текста:', err)
  } finally {
    resettingText.value = false
  }
}
</script>
