<template>
  <v-card>
    <v-card-title class="text-subtitle-1">Добавить страницы</v-card-title>
    <v-card-text>
      <div
        class="upload-dropzone"
        :class="{ 'upload-dropzone--active': isDragOver }"
        @dragover.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        @drop.prevent="handleFileDrop"
        @click="fileInputEl.click()"
      >
        <v-icon size="22">mdi-tray-arrow-up</v-icon>
        <div class="text-caption">Перетащите файлы или нажмите, чтобы выбрать</div>
        <input
          ref="fileInputEl"
          type="file"
          multiple
          :accept="allowedExtensions.join(',')"
          style="display:none"
          @change="handleFileInputChange"
        >
      </div>

      <v-row v-if="sortedPageFiles.length" dense class="mt-2">
        <v-col v-for="entry in sortedPageFiles" :key="entry.name" cols="4" sm="3" md="2">
          <v-card variant="outlined" class="upload-preview-card">
            <v-img :src="entry.url" height="70" cover></v-img>
            <v-btn
              icon="mdi-close"
              size="x-small"
              density="compact"
              variant="flat"
              color="grey-darken-3"
              class="upload-preview-remove"
              @click.stop="removeFile(entry.file)"
            ></v-btn>
            <div class="text-caption text-truncate px-1">{{ entry.name }}</div>
          </v-card>
        </v-col>
      </v-row>

      <PageNumberField
        v-model="position"
        label="Номер страницы, после которой вставить (0 - в начало)"
        class="mt-2"
        :min="0"
        :max="pageCount"
      ></PageNumberField>
      <v-alert v-if="uploadError" type="error" density="compact">{{ uploadError }}</v-alert>
      <v-alert v-if="rejectedFiles.length" type="warning" density="compact">
        Не приняты (недопустимый формат): {{ rejectedFiles.join(', ') }}
      </v-alert>
      <v-alert v-if="acceptedFiles.length" type="success" density="compact">
        Загружено: {{ acceptedFiles.join(', ') }}
      </v-alert>
    </v-card-text>
    <v-card-actions>
      <v-btn
        color="primary"
        :loading="uploadingPages"
        :disabled="!canUploadPages"
        @click="handleUploadPages"
      >Загрузить страницы</v-btn>
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

<style scoped>
.upload-dropzone {
  border: 2px dashed rgba(128, 128, 128, 0.5);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: border-color .15s, background-color .15s;
}
.upload-dropzone--active {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.08);
}
.upload-preview-card {
  position: relative;
}
.upload-preview-remove {
  position: absolute;
  top: 2px;
  right: 2px;
}
</style>
