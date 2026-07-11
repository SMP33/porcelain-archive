<template>
  <v-layout>
    <AppToolbar />
    <v-main>
      <v-container>
        <v-card v-if="!loading && document">
          <v-card-title>
            {{ document.name }}
          </v-card-title>
          <v-card-subtitle>
            Автор: {{ document.author }} | Создан: {{ document.created_at }}
          </v-card-subtitle>
          <v-card-text>
            <p>Это страница для просмотра документа с ID: <strong>{{ document.id }}</strong>.</p>
            <p>Здесь будет содержимое документа.</p>
          </v-card-text>
          <v-card-actions>
            <v-btn color="primary" to="/">Назад к списку</v-btn>
            <v-btn v-if="user" color="secondary" :loading="creatingBranch" @click="handleEditDocument">Редактировать документ</v-btn>
          </v-card-actions>
          <v-alert v-if="editError" type="error" density="compact">{{ editError }}</v-alert>
        </v-card>

        <v-card v-if="!loading && document && masterBranchId" class="mt-4">
          <v-card-title class="text-subtitle-1">Страницы</v-card-title>
          <v-card-text>
            <v-progress-circular v-if="galleryLoading" indeterminate size="20"></v-progress-circular>
            <div v-else-if="!galleryPageCount" class="text-medium-emphasis">Страниц пока нет</div>
            <v-row v-else dense>
              <v-col v-for="pos in galleryPageCount" :key="pos" cols="6" sm="4" md="3" lg="2">
                <v-card variant="outlined" class="gallery-thumb" @click="galleryRef.show(pos)">
                  <v-img :src="galleryRef && galleryRef.previewImageUrl(pos)" height="120" cover></v-img>
                  <div class="text-caption text-center pa-1">{{ pos }}</div>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <PageGalleryViewer
          v-if="masterBranchId"
          ref="galleryRef"
          :branch-id="masterBranchId"
          :page-count="galleryPageCount"
        />

        <v-progress-circular v-if="loading" indeterminate color="primary"></v-progress-circular>
        <v-alert v-if="error" type="error">{{ error }}</v-alert>
      </v-container>
    </v-main>
  </v-layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'
import PageGalleryViewer from '../components/PageGalleryViewer.vue'

const route = useRoute()
const router = useRouter()
const { user } = useAuth()

const document = ref(null)
const loading = ref(true)
const error = ref(null)

const creatingBranch = ref(false)
const editError = ref('')

const masterBranchId = ref(null)
const galleryPageCount = ref(0)
const galleryLoading = ref(true)
const galleryRef = ref(null)

const loadDocument = async (id) => {
  try {
    const response = await http.get(`/api/documents/${id}`)
    document.value = response.data
  } catch (err) {
    const status = err.response ? err.response.status : null
    if (status === 401) {
      router.push({ name: 'login', query: { redirect: route.fullPath } })
      return
    }
    if (status === 403 || status === 404) {
      router.push('/access-denied')
      return
    }
    error.value = 'Не удалось загрузить документ.'
    console.error('Ошибка при загрузке документа:', err)
  } finally {
    loading.value = false
  }
}

const loadGallery = async () => {
  galleryLoading.value = true
  try {
    const branchResponse = await http.get(`/api/documents/${document.value.id}/master_branch_id`)
    masterBranchId.value = branchResponse.data.branch_id

    const countResponse = await http.get(`/api/documents/branches/${masterBranchId.value}/pages/count`)
    galleryPageCount.value = countResponse.data.count
  } catch (err) {
    console.error('Ошибка при получении страниц документа:', err)
  } finally {
    galleryLoading.value = false
  }
}

const handleEditDocument = async () => {
  creatingBranch.value = true
  editError.value = ''
  try {
    const response = await http.post(`/api/documents/${document.value.id}/create_branch`, {})
    router.push(`/edit/${response.data.branch_id}`)
  } catch (err) {
    editError.value = 'Не удалось создать набор изменений для редактирования.'
    console.error('Ошибка при создании ветки:', err)
  } finally {
    creatingBranch.value = false
  }
}

onMounted(async () => {
  await loadDocument(route.params.documentId)
  if (document.value) {
    loadGallery()
  }
})
</script>

<style scoped>
.gallery-thumb {
  cursor: pointer;
}
</style>
