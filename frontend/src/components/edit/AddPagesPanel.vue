<template>
  <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
    <h2 class="tw:font-serif tw:font-semibold tw:text-ink-900 tw:mb-4">Добавить страницы</h2>

    <div
      class="tw:border-2 tw:border-dashed tw:rounded-lg tw:p-4 tw:text-center tw:cursor-pointer tw:transition-colors"
      :class="isDragOver ? 'tw:border-clay-400 tw:bg-clay-50' : 'tw:border-gray-300'"
      @dragover.prevent="isDragOver = true"
      @dragleave.prevent="isDragOver = false"
      @drop.prevent="handleFileDrop"
      @click="fileInputEl.click()"
    >
      <i class="mdi mdi-tray-arrow-up tw:text-2xl tw:text-gray-400" />
      <div class="tw:text-xs tw:text-gray-500 tw:mt-1">Перетащите файлы или нажмите, чтобы выбрать</div>
      <input
        ref="fileInputEl"
        type="file"
        multiple
        :accept="allowedExtensions.join(',')"
        class="tw:hidden"
        @change="handleFileInputChange"
      >
    </div>

    <div v-if="sortedPageFiles.length" class="tw:grid tw:grid-cols-4 tw:sm:grid-cols-6 tw:gap-2 tw:mt-3">
      <div v-for="entry in sortedPageFiles" :key="entry.name" class="tw:relative tw:border tw:border-gray-200 tw:rounded tw:overflow-hidden">
        <img :src="entry.url" class="tw:w-full tw:h-[70px] tw:object-cover">
        <button
          type="button"
          class="tw:absolute tw:top-0.5 tw:right-0.5 tw:w-5 tw:h-5 tw:flex tw:items-center tw:justify-center tw:bg-gray-800/70 tw:hover:bg-gray-800 tw:text-white tw:rounded-full tw:transition-colors"
          @click.stop="removeFile(entry.file)"
        >
          <i class="mdi mdi-close tw:text-xs" />
        </button>
        <div class="tw:text-[11px] tw:text-gray-500 tw:truncate tw:px-1">{{ entry.name }}</div>
      </div>
    </div>

    <PageNumberField
      v-model="position"
      label="Номер страницы, после которой вставить (0 - в начало)"
      class="tw:mt-3"
      :min="0"
      :max="pageCount"
    />
    <div v-if="uploadError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      {{ uploadError }}
    </div>
    <div v-if="rejectedFiles.length" class="tw:text-sm tw:text-amber-700 tw:bg-amber-50 tw:border tw:border-amber-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      Не приняты (недопустимый формат): {{ rejectedFiles.join(', ') }}
    </div>
    <div v-if="acceptedFiles.length" class="tw:text-sm tw:text-green-700 tw:bg-green-50 tw:border tw:border-green-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
      Загружено: {{ acceptedFiles.join(', ') }}
    </div>

    <button
      type="button"
      :disabled="!canUploadPages || uploadingPages"
      class="tw:mt-4 tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
      @click="handleUploadPages"
    >
      {{ uploadingPages ? 'Загрузка…' : 'Загрузить страницы' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import http from '../../api/http'
import PageNumberField from '../PageNumberField.vue'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
  pageCount: { type: Number, required: true },
  allowedExtensions: { type: Array, required: true },
})

const emit = defineEmits(['uploaded'])

const pageFiles = ref([])
const position = ref(props.pageCount)
const uploadingPages = ref(false)
const uploadError = ref('')
const acceptedFiles = ref([])
const rejectedFiles = ref([])
const isDragOver = ref(false)
const fileInputEl = ref(null)

watch(() => props.pageCount, (count) => {
  position.value = count
}, { immediate: true })

const handleFileInputChange = (event) => {
  if (event.target.files && event.target.files.length) {
    pageFiles.value = [...pageFiles.value, ...Array.from(event.target.files)]
  }
  event.target.value = ''
}

const handleFileDrop = (event) => {
  isDragOver.value = false
  if (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files.length) {
    pageFiles.value = [...pageFiles.value, ...Array.from(event.dataTransfer.files)]
  }
}

const removeFile = (file) => {
  pageFiles.value = pageFiles.value.filter((f) => f !== file)
}

const canUploadPages = computed(() => {
  if (!pageFiles.value.length) return false
  if (position.value === '' || position.value === null) return false
  return Number.isInteger(position.value) && position.value >= 0 && position.value <= props.pageCount
})

// Позиция вставки (после какой страницы) - используется EditView для подсветки
// места между плитками, куда будут вставлены новые страницы.
const insertGapPosition = computed(() => {
  if (position.value === '' || position.value === null) return null
  if (!Number.isInteger(position.value) || position.value < 0 || position.value > props.pageCount) return null
  return position.value
})

defineExpose({ insertGapPosition })

// Сортировка по имени файла с учётом чисел (page2 раньше page10)
const sortedPageFiles = computed(() => {
  return [...pageFiles.value]
    .sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }))
    .map((file) => ({ file, name: file.name, url: URL.createObjectURL(file) }))
})

watch(sortedPageFiles, (_entries, previousEntries) => {
  previousEntries?.forEach((entry) => URL.revokeObjectURL(entry.url))
})

const handleUploadPages = async () => {
  uploadingPages.value = true
  uploadError.value = ''
  acceptedFiles.value = []
  rejectedFiles.value = []
  try {
    const formData = new FormData()
    for (const entry of sortedPageFiles.value) {
      formData.append('files', entry.file)
    }
    formData.append('position', String(position.value))
    const response = await http.post(
      `/api/documents/branches/${props.branchId}/pages`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    acceptedFiles.value = response.data.accepted
    rejectedFiles.value = response.data.rejected
    pageFiles.value = []
    emit('uploaded')
  } catch (err) {
    uploadError.value = 'Не удалось загрузить страницы.'
    console.error('Ошибка при загрузке страниц:', err)
  } finally {
    uploadingPages.value = false
  }
}
</script>
