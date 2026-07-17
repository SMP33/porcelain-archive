<template>
  <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
    <h2 class="tw:font-serif tw:font-semibold tw:text-ink-900 tw:mb-4">Удалить страницы</h2>
    <div class="tw:grid tw:grid-cols-2 tw:gap-3">
      <PageNumberField
        v-model="removeStart"
        label="Со страницы"
        :min="1"
        :max="pageCount"
        @focus="focusedField = 'start'"
      />
      <PageNumberField
        v-model="removeEnd"
        label="По страницу"
        :min="removeStart || 1"
        :max="pageCount"
        @focus="focusedField = 'end'"
      />
    </div>
    <div v-if="removeError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      {{ removeError }}
    </div>
    <div v-if="removeSuccess" class="tw:text-sm tw:text-green-700 tw:bg-green-50 tw:border tw:border-green-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      Задача на удаление страниц поставлена в очередь.
    </div>
    <button
      type="button"
      :disabled="!canRemovePages || removingPages"
      class="tw:mt-4 tw:px-5 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
      @click="handleRemovePages"
    >
      {{ removingPages ? 'Удаление…' : 'Удалить страницы' }}
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

const emit = defineEmits(['removed'])

const removeStart = ref(null)
const removeEnd = ref(null)
const removingPages = ref(false)
const removeError = ref('')
const removeSuccess = ref(false)
const focusedField = ref(null)

const canRemovePages = computed(() => {
  if (!props.pageCount) return false
  const start = removeStart.value
  const end = removeEnd.value
  if (!Number.isInteger(start) || !Number.isInteger(end)) return false
  return start >= 1 && end >= start && end <= props.pageCount
})

// Диапазон удаляемых страниц - используется EditView для подсветки плиток.
// Подсвечивается сразу по мере ввода, не дожидаясь заполнения обоих полей -
// незаполненное поле считается равным заполненному.
const highlightRange = computed(() => {
  const start = Number.isInteger(removeStart.value) ? removeStart.value : null
  const end = Number.isInteger(removeEnd.value) ? removeEnd.value : null
  if (start == null && end == null) return null
  const rangeStart = start ?? end
  const rangeEnd = end ?? start
  return { start: Math.min(rangeStart, rangeEnd), end: Math.max(rangeStart, rangeEnd) }
})

// Страница, которую нужно показать в области плиток - зависит от того, какое
// поле сейчас в фокусе (начало или конец диапазона).
const scrollTargetPos = computed(() => {
  const pos = focusedField.value === 'start' ? removeStart.value : focusedField.value === 'end' ? removeEnd.value : null
  return Number.isInteger(pos) ? pos : null
})

defineExpose({ highlightRange, scrollTargetPos })

const handleRemovePages = async () => {
  removingPages.value = true
  removeError.value = ''
  removeSuccess.value = false
  try {
    await http.post(`/api/documents/branches/${props.branchId}/pages/remove`, {
      start: removeStart.value,
      end: removeEnd.value,
    })
    removeSuccess.value = true
    emit('removed')
  } catch (err) {
    removeError.value = 'Не удалось удалить страницы.'
    console.error('Ошибка при удалении страниц:', err)
  } finally {
    removingPages.value = false
  }
}
</script>
