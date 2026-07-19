<template>
  <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
    <h2 class="tw:font-serif tw:font-semibold tw:text-ink-900 tw:mb-4">Задать текст</h2>

    <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">PDF-файл</label>
    <input
      type="file"
      accept=".pdf"
      class="tw:w-full tw:text-sm tw:text-gray-500 tw:file:mr-3 tw:file:py-1.5 tw:file:px-3 tw:file:rounded tw:file:border tw:file:border-gray-200 tw:file:text-xs tw:file:bg-gray-50 tw:file:hover:bg-gray-100 tw:file:transition-colors tw:cursor-pointer"
      @change="onFileChange"
    >
    <div v-if="textFile" class="tw:text-xs tw:text-gray-400 tw:mt-1">{{ textFile.name }} · {{ formatSize(textFile.size) }}</div>

    <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1 tw:mt-3">Качество распознавания</label>
    <AppListbox v-model="ocrQuality" :options="ocrQualityOptions" />

    <PageNumberField
      v-model="textPosition"
      label="Страница, с которой применяется текст"
      class="tw:mt-3"
      :min="1"
      :max="pageCount"
    />
    <div v-if="hasExtraPdfPages" class="tw:text-sm tw:text-amber-700 tw:bg-amber-50 tw:border tw:border-amber-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      PDF содержит {{ pdfPageCount }} страниц(ы), а начиная с позиции {{ textPosition }}
      в наборе изменений помещается только {{ availableSlots }}. Лишние страницы PDF
      будут отброшены.
    </div>
    <div v-if="setTextError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      {{ setTextError }}
    </div>
    <div v-if="setTextSuccess" class="tw:text-sm tw:text-green-700 tw:bg-green-50 tw:border tw:border-green-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      Задача на применение текста поставлена в очередь.
    </div>

    <button
      type="button"
      :disabled="!canSetText || settingText"
      class="tw:mt-4 tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
      @click="handleSetText"
    >
      {{ settingText ? 'Отправка…' : 'Задать текст' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import http from '../../api/http'
import PageNumberField from '../PageNumberField.vue'
import AppListbox from '../AppListbox.vue'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorkerUrl

const props = defineProps({
  branchId: { type: [Number, String], required: true },
  pageCount: { type: Number, required: true },
})

const emit = defineEmits(['submitted'])

const textFile = ref(null)
const ocrQualityOptions = [
  { value: 'high', title: 'Высокое' },
  { value: 'low', title: 'Низкое' },
  { value: 'worst', title: 'Очень низкое' },
]
const ocrQuality = ref('high')
const textPosition = ref(props.pageCount ? 1 : 0)
const settingText = ref(false)
const setTextError = ref('')
const setTextSuccess = ref(false)
const pdfPageCount = ref(null)

watch(() => props.pageCount, (count) => {
  textPosition.value = count ? 1 : 0
}, { immediate: true })

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} Б`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`
}

function onFileChange(event) {
  textFile.value = event.target.files && event.target.files[0] ? event.target.files[0] : null
}

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
  readPdfPageCount(value)
})

const handleSetText = async () => {
  settingText.value = true
  setTextError.value = ''
  setTextSuccess.value = false
  try {
    const formData = new FormData()
    formData.append('file', textFile.value)
    formData.append('position', String(textPosition.value))
    formData.append('ocr_quality', ocrQuality.value)
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
