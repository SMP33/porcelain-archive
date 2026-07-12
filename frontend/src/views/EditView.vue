<template>
  <v-layout>
    <AppToolbar />
    <v-main>
      <v-container fluid>
        <v-card v-if="!loading && branch">
          <v-card-title class="d-flex justify-space-between align-center">
            <span>{{ branch.documentName }}</span>
            <v-select
              v-if="hasRole('moderator')"
              :model-value="branch.status"
              @update:model-value="handleSetStatus"
              :items="statusOptions"
              item-title="title"
              item-value="value"
              density="compact"
              hide-details
              style="max-width: 220px"
              :loading="statusLoading"
            >
              <template v-slot:selection="{ item }">
                <span :style="{ color: statusColors[item.value] || 'grey' }">{{ item.title }}</span>
              </template>
              <template v-slot:item="{ item, props }">
                <v-list-item v-bind="props" title="">
                  <span :style="{ color: statusColors[item.value] || 'grey' }">{{ item.title }}</span>
                </v-list-item>
              </template>
            </v-select>
            <v-chip v-else :color="statusColors[branch.status] || 'grey'">
              {{ statusLabels[branch.status] || branch.status }}
            </v-chip>
          </v-card-title>
          <v-card-subtitle>
            № {{ branch.id }}
          </v-card-subtitle>
          <v-card-text>
            <p>Это страница редактирования набора изменений с ID: <strong>{{ branch.id }}</strong>.</p>
            <p>Страниц в наборе изменений: <strong>{{ pageCount }}</strong></p>
          </v-card-text>
          <v-card-actions>
            <v-btn color="primary" to="/">Назад к списку</v-btn>
            <v-btn
              v-if="isAuthor && branch.status === 'in_work'"
              color="primary"
              :loading="statusActionLoading"
              @click="handleSubmitForReview"
            >Отправить на проверку</v-btn>
            <v-btn
              v-if="isAuthor && branch.status === 'in_review'"
              color="secondary"
              :loading="statusActionLoading"
              @click="handleReturnToWork"
            >Вернуть в работу</v-btn>
            <v-btn
              v-if="hasRole('moderator') && branch.status === 'accepted'"
              color="success"
              @click="mergeDialogRef.open()"
            >Завершить правки</v-btn>
          </v-card-actions>
        </v-card>

        <MergeBranchDialog
          v-if="branch"
          ref="mergeDialogRef"
          :branch-id="branch.id"
          @merged="branchTasksRef.reload()"
        />

        <v-row v-if="!loading && branch" class="mt-1">
          <v-col cols="12" md="2">
            <v-card>
              <v-list density="compact" nav>
                <v-list-item
                  title="Добавить страницы"
                  prepend-icon="mdi-file-plus"
                  :active="activeView === 'add'"
                  @click="activeView = 'add'"
                ></v-list-item>
                <v-list-item
                  title="Удалить страницы"
                  prepend-icon="mdi-file-remove"
                  :active="activeView === 'remove'"
                  @click="activeView = 'remove'"
                ></v-list-item>
                <v-list-item
                  title="Задать текст"
                  prepend-icon="mdi-file-pdf-box"
                  :active="activeView === 'set_text'"
                  @click="activeView = 'set_text'"
                ></v-list-item>
                <v-list-item
                  title="Убрать текст"
                  prepend-icon="mdi-text-box-remove"
                  :active="activeView === 'reset_text'"
                  @click="activeView = 'reset_text'"
                ></v-list-item>
              </v-list>
            </v-card>
          </v-col>

          <v-col cols="12" md="7">
            <AddPagesPanel
              v-if="activeView === 'add'"
              :branch-id="branch.id"
              :page-count="pageCount"
              :allowed-extensions="allowedExtensions"
              @uploaded="onPagesChanged"
            />

            <RemovePagesPanel
              v-if="activeView === 'remove'"
              :branch-id="branch.id"
              :page-count="pageCount"
              @removed="onPagesChanged"
            />

            <SetTextPanel
              v-if="activeView === 'set_text'"
              :branch-id="branch.id"
              :page-count="pageCount"
              @submitted="branchTasksRef.reload()"
            />

            <ResetTextPanel
              v-if="activeView === 'reset_text'"
              :branch-id="branch.id"
              :page-count="pageCount"
              @submitted="branchTasksRef.reload()"
            />

            <v-card class="mt-4">
              <v-card-title class="text-subtitle-1">Страницы</v-card-title>
              <v-card-text>
                <div v-if="!pageCount" class="text-medium-emphasis">Страниц пока нет</div>
                <v-row v-else dense>
                  <v-col v-for="pos in pageCount" :key="pos" cols="6" sm="4" md="3" lg="2">
                    <v-card variant="outlined" class="gallery-thumb" @click="galleryRef.show(pos)">
                      <v-img :src="galleryRef && galleryRef.previewImageUrl(pos)" height="120" cover></v-img>
                      <div class="text-caption text-center pa-1">{{ pos }}</div>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="3">
            <BranchTasksPanel ref="branchTasksRef" :branch-id="branch.id" />
          </v-col>
        </v-row>

        <PageGalleryViewer
          v-if="branch"
          ref="galleryRef"
          :branch-id="branch.id"
          :page-count="pageCount"
        />

        <v-progress-circular v-if="loading" indeterminate color="primary"></v-progress-circular>
        <v-alert v-if="error" type="error">{{ error }}</v-alert>
      </v-container>
    </v-main>
  </v-layout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'
import PageGalleryViewer from '../components/PageGalleryViewer.vue'
import MergeBranchDialog from '../components/edit/MergeBranchDialog.vue'
import AddPagesPanel from '../components/edit/AddPagesPanel.vue'
import RemovePagesPanel from '../components/edit/RemovePagesPanel.vue'
import SetTextPanel from '../components/edit/SetTextPanel.vue'
import ResetTextPanel from '../components/edit/ResetTextPanel.vue'
import BranchTasksPanel from '../components/edit/BranchTasksPanel.vue'

const route = useRoute()
const router = useRouter()
const { user, hasRole } = useAuth()

const statusLabels = {
  in_work: 'В работе',
  in_review: 'Проверяется',
  accepted: 'Принято',
  rejected: 'Отклонено',
}
const statusColors = {
  in_work: 'blue',
  in_review: '#b39ddb',
  accepted: 'green',
  rejected: 'red',
}
const statusOptions = Object.entries(statusLabels).map(([value, title]) => ({ value, title }))

const branch = ref(null)
const loading = ref(true)
const error = ref(null)

const pageCount = ref(0)
const allowedExtensions = ref([])
const activeView = ref('add')

const statusLoading = ref(false)
const statusActionLoading = ref(false)

const mergeDialogRef = ref(null)
const branchTasksRef = ref(null)
const galleryRef = ref(null)

const isAuthor = computed(() => !!(user.value && branch.value && user.value.id === branch.value.authorId))

let ws = null
let wsShouldReconnect = true

const loadBranch = async (id) => {
  try {
    const response = await http.get(`/api/documents/branches/${id}`)
    branch.value = {
      id: response.data.id,
      documentName: response.data.document_name,
      authorId: response.data.author_id,
      status: response.data.status,
    }
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
    error.value = 'Не удалось загрузить набор изменений.'
    console.error('Ошибка при загрузке набора изменений:', err)
  } finally {
    loading.value = false
  }
}

const loadPageCount = async () => {
  try {
    const response = await http.get(`/api/documents/branches/${branch.value.id}/pages/count`)
    pageCount.value = response.data.count
  } catch (err) {
    console.error('Ошибка при получении количества страниц:', err)
  }
}

const loadAllowedExtensions = async () => {
  try {
    const response = await http.get('/api/documents/pages/allowed_extensions')
    allowedExtensions.value = response.data.extensions
  } catch (err) {
    console.error('Ошибка при получении списка допустимых расширений:', err)
  }
}

const handleSubmitForReview = async () => {
  statusActionLoading.value = true
  try {
    await http.post(`/api/documents/branches/${branch.value.id}/submit_for_review`, {})
    branch.value.status = 'in_review'
  } catch (err) {
    console.error('Ошибка при отправке на проверку:', err)
  } finally {
    statusActionLoading.value = false
  }
}

const handleReturnToWork = async () => {
  statusActionLoading.value = true
  try {
    await http.post(`/api/documents/branches/${branch.value.id}/return_to_work`, {})
    branch.value.status = 'in_work'
  } catch (err) {
    console.error('Ошибка при возврате в работу:', err)
  } finally {
    statusActionLoading.value = false
  }
}

const handleSetStatus = async (newStatus) => {
  statusLoading.value = true
  try {
    await http.post(`/api/documents/branches/${branch.value.id}/status`, { status: newStatus })
    branch.value.status = newStatus
  } catch (err) {
    console.error('Ошибка при изменении статуса:', err)
  } finally {
    statusLoading.value = false
  }
}

const onPagesChanged = async () => {
  await loadPageCount()
  branchTasksRef.value.reload()
}

const connectTaskUpdates = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${window.location.host}/api/tasks/ws`)

  ws.onmessage = async () => {
    branchTasksRef.value.reload()
    loadPageCount()
  }

  ws.onclose = () => {
    if (wsShouldReconnect) {
      setTimeout(connectTaskUpdates, 2000)
    }
  }
}

onMounted(async () => {
  await loadBranch(route.params.branchId)
  if (branch.value) {
    loadPageCount()
    loadAllowedExtensions()
    connectTaskUpdates()
  }
})

onUnmounted(() => {
  wsShouldReconnect = false
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.gallery-thumb {
  cursor: pointer;
}
</style>
