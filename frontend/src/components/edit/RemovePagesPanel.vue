<template>
  <v-card>
    <v-card-title class="text-subtitle-1">Удалить страницы</v-card-title>
    <v-card-text>
      <v-row dense>
        <v-col cols="6">
          <PageNumberField
            v-model="removeStart"
            label="С страницы"
            :min="1"
            :max="pageCount"
          ></PageNumberField>
        </v-col>
        <v-col cols="6">
          <PageNumberField
            v-model="removeEnd"
            label="По страницу"
            :min="removeStart || 1"
            :max="pageCount"
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
import { ref, computed, watch } from 'vue'
import http from '../../api/http'
import PageNumberField from '../PageNumberField.vue'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
  pageCount: { type: Number, required: true },
})

const emit = defineEmits(['removed'])

const removeStart = ref(props.pageCount ? 1 : 0)
const removeEnd = ref(props.pageCount)
const removingPages = ref(false)
const removeError = ref('')
const removeSuccess = ref(false)

watch(() => props.pageCount, (count) => {
  removeStart.value = count ? 1 : 0
  removeEnd.value = count
}, { immediate: true })

const canRemovePages = computed(() => {
  if (!props.pageCount) return false
  const start = removeStart.value
  const end = removeEnd.value
  if (!Number.isInteger(start) || !Number.isInteger(end)) return false
  return start >= 1 && end >= start && end <= props.pageCount
})

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
