<template>
  <v-card>
    <v-card-title class="text-subtitle-1">Задать текст</v-card-title>
    <v-card-text>
      <v-file-input
        v-model="textFile"
        label="PDF-файл"
        accept=".pdf"
        density="compact"
        prepend-icon="mdi-file-pdf-box"
        show-size
      ></v-file-input>

      <PageNumberField
        v-model="textPosition"
        label="Страница, с которой применяется текст"
        class="mt-2"
        :min="1"
        :max="pageCount"
      ></PageNumberField>
      <v-alert v-if="setTextError" type="error" density="compact">{{ setTextError }}</v-alert>
      <v-alert v-if="setTextSuccess" type="success" density="compact">
        Задача на применение текста поставлена в очередь.
      </v-alert>
    </v-card-text>
    <v-card-actions>
      <v-btn
        color="primary"
        :loading="settingText"
        :disabled="!canSetText"
        @click="handleSetText"
      >Задать текст</v-btn>
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

const emit = defineEmits(['submitted'])

const textFile = ref(null)
const textPosition = ref(props.pageCount ? 1 : 0)
const settingText = ref(false)
const setTextError = ref('')
const setTextSuccess = ref(false)

watch(() => props.pageCount, (count) => {
  textPosition.value = count ? 1 : 0
}, { immediate: true })

const canSetText = computed(() => {
  if (!textFile.value) return false
  if (!props.pageCount) return false
  const pos = textPosition.value
  return Number.isInteger(pos) && pos >= 1 && pos <= props.pageCount
})

const handleSetText = async () => {
  settingText.value = true
  setTextError.value = ''
  setTextSuccess.value = false
  try {
    const file = Array.isArray(textFile.value) ? textFile.value[0] : textFile.value
    const formData = new FormData()
    formData.append('file', file)
    formData.append('position', String(textPosition.value))
    await http.post(`/api/documents/branches/${props.branchId}/text`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    setTextSuccess.value = true
    textFile.value = null
    emit('submitted')
  } catch (err) {
    setTextError.value = 'Не удалось поставить задачу в очередь.'
    console.error('Ошибка при загрузке текста:', err)
  } finally {
    settingText.value = false
  }
}
</script>
