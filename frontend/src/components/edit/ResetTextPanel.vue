<template>
  <v-card>
    <v-card-title class="text-subtitle-1">Убрать текст</v-card-title>
    <v-card-text>
      <v-row dense>
        <v-col cols="6">
          <PageNumberField
            v-model="resetTextStart"
            label="Со страницы"
            :min="1"
            :max="pageCount"
            @focus="focusedField = 'start'"
          ></PageNumberField>
        </v-col>
        <v-col cols="6">
          <PageNumberField
            v-model="resetTextEnd"
            label="По страницу"
            :min="resetTextStart || 1"
            :max="pageCount"
            @focus="focusedField = 'end'"
          ></PageNumberField>
        </v-col>
      </v-row>
      <v-alert v-if="resetTextError" type="error" density="compact">{{ resetTextError }}</v-alert>
      <v-alert v-if="resetTextSuccess" type="success" density="compact">
        Задача на удаление текста поставлена в очередь.
      </v-alert>
    </v-card-text>
    <v-card-actions>
      <v-btn
        color="error"
        :loading="resettingText"
        :disabled="!canResetText"
        @click="handleResetText"
      >Убрать текст</v-btn>
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
