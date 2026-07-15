<template>
  <v-card>
    <v-card-title class="text-subtitle-1">Удалить страницы</v-card-title>
    <v-card-text>
      <v-row dense>
        <v-col cols="6">
          <PageNumberField
            v-model="removeStart"
            label="Со страницы"
            :min="1"
            :max="pageCount"
            @focus="focusedField = 'start'"
          ></PageNumberField>
        </v-col>
        <v-col cols="6">
          <PageNumberField
            v-model="removeEnd"
            label="По страницу"
            :min="removeStart || 1"
            :max="pageCount"
            @focus="focusedField = 'end'"
          ></PageNumberField>
        </v-col>
      </v-row>
      <v-alert v-if="removeError" type="error" density="compact">{{ removeError }}</v-alert>
      <v-alert v-if="removeSuccess" type="success" density="compact">
        Задача на удаление страниц поставлена в очередь.
      </v-alert>
    </v-card-text>
    <v-card-actions>
      <v-btn
        color="error"
        :loading="removingPages"
        :disabled="!canRemovePages"
        @click="handleRemovePages"
      >Удалить страницы</v-btn>
    </v-card-actions>
  </v-card>
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
