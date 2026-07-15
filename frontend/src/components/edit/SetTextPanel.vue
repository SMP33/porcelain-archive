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
      <v-alert v-if="hasExtraPdfPages" type="warning" density="compact" class="mt-2">
        PDF содержит {{ pdfPageCount }} страниц(ы), а начиная с позиции {{ textPosition }}
        в наборе изменений помещается только {{ availableSlots }}. Лишние страницы PDF
        будут отброшены.
      </v-alert>
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
import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import http from '../../api/http'
import PageNumberField from '../PageNumberField.vue'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorkerUrl

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
const pdfPageCount = ref(null)

watch(() => props.pageCount, (count) => {
  textPosition.value = count ? 1 : 0
}, { immediate: true })

const canSetText = computed(() => {
  if (!textFile.value) return false
  if (!props.pageCount) return false
  const pos = textPosition.value
  return Number.isInteger(pos) && pos >= 1 && pos <= props.pageCount
})

const availableSlots = computed(() => {
  const pos = textPosition.value
  if (!props.pageCount || !Number.isInteger(pos) || pos < 1) return 0
  return props.pageCount - pos + 1
})

const hasExtraPdfPages = computed(() => (
  pdfPageCount.value != null && pdfPageCount.value > availableSlots.value
))

// Страница, с которой применяется текст - используется EditView для подсветки плитки.
const highlightRange = computed(() => {
  const pos = textPosition.value
  if (!props.pageCount || !Number.isInteger(pos) || pos < 1 || pos > props.pageCount) return null
  return { start: pos, end: pos }
})

defineExpose({ highlightRange })

const readPdfPageCount = async (file) => {
  pdfPageCount.value = null
  if (!file) return
  try {
    const buffer = await file.arrayBuffer()
    const pdfDocument = await pdfjsLib.getDocument({ data: buffer }).promise
    pdfPageCount.value = pdfDocument.numPages
  } catch (err) {
    console.error('Ошибка при проверке количества страниц PDF:', err)
  }
}

watch(textFile, (value) => {
  readPdfPageCount(Array.isArray(value) ? value[0] : value)
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
