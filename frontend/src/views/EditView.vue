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
              @update:model-value="requestSetStatus"
              :items="statusOptions"
              item-title="title"
              item-value="value"
              density="compact"
              hide-details
              style="max-width: 220px"
              :loading="statusLoading"
              :disabled="isLocked"
            >
              <template v-slot:selection="{ item }">
                <span :style="{ color: statusColors[item.value] || 'grey' }">{{ item.title }}</span>
              </template>
              <template v-slot:item="{ item, props }">
                <v-list-item v-bind="props" :disabled="item.value === 'accepted'" title="">
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
          </v-card-actions>
        </v-card>

        <v-dialog v-model="confirmStatusDialog" max-width="480">
          <v-card>
            <v-card-title>Подтверждение изменения статуса</v-card-title>
            <v-card-text>
              Изменить статус набора изменений № {{ branch && branch.id }} на «<span :style="{ color: statusColors[pendingStatus] || 'grey' }">{{ statusLabels[pendingStatus] }}</span>»?
              <template v-if="pendingStatus === 'in_accept'">
                <br>Изменения будут автоматически слиты в основную версию документа.
              </template>
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn @click="cancelSetStatus">Отмена</v-btn>
              <v-btn color="primary" :loading="statusLoading" :disabled="!confirmReady" @click="confirmSetStatus">Подтвердить</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <v-row v-if="!loading && branch" class="mt-1">
          <v-col cols="auto">
            <v-card class="edit-view-menu-card">
              <v-list density="compact" nav class="edit-view-menu">
                <v-list-item
                  v-if="!isLocked"
                  prepend-icon="mdi-file-plus"
                  :active="activeView === 'add'"
                  @click="activeView = 'add'"
                ><span class="edit-view-menu-label">Добавить страницы</span></v-list-item>
                <v-list-item
                  v-if="!isLocked"
                  prepend-icon="mdi-file-remove"
                  :active="activeView === 'remove'"
                  @click="activeView = 'remove'"
                ><span class="edit-view-menu-label">Удалить страницы</span></v-list-item>
                <v-list-item
                  v-if="!isLocked"
                  prepend-icon="mdi-file-pdf-box"
                  :active="activeView === 'set_text'"
                  @click="activeView = 'set_text'"
                ><span class="edit-view-menu-label">Задать текст</span></v-list-item>
                <v-list-item
                  v-if="!isLocked"
                  prepend-icon="mdi-text-box-remove"
                  :active="activeView === 'reset_text'"
                  @click="activeView = 'reset_text'"
                ><span class="edit-view-menu-label">Убрать текст</span></v-list-item>
                <v-list-item
                  prepend-icon="mdi-compare"
                  :active="activeView === 'view_changes'"
                  @click="activeView = 'view_changes'"
                ><span class="edit-view-menu-label">Просмотр изменений</span></v-list-item>
              </v-list>
            </v-card>
          </v-col>

          <v-col>
            <AddPagesPanel
              v-if="!isLocked && activeView === 'add'"
              :branch-id="branch.id"
              :page-count="pageCount"
              :allowed-extensions="allowedExtensions"
              @uploaded="onPagesChanged"
            />

            <RemovePagesPanel
              v-if="!isLocked && activeView === 'remove'"
              :branch-id="branch.id"
              :page-count="pageCount"
              @removed="onPagesChanged"
            />

            <SetTextPanel
              v-if="!isLocked && activeView === 'set_text'"
              :branch-id="branch.id"
              :page-count="pageCount"
              @submitted="branchTasksRef.reload()"
            />

            <ResetTextPanel
              v-if="!isLocked && activeView === 'reset_text'"
              :branch-id="branch.id"
              :page-count="pageCount"
              @submitted="branchTasksRef.reload()"
            />

            <ViewChangesPanel
              v-if="activeView === 'view_changes'"
              :branch-id="branch.id"
              :initial-commit="branch.initialCommit"
              :last-commit="branch.lastCommit"
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

          <v-col cols="12" md="2">
            <BranchTasksPanel
              ref="branchTasksRef"
              :branch-id="branch.id"
            />
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'
import PageGalleryViewer from '../components/PageGalleryViewer.vue'
import AddPagesPanel from '../components/edit/AddPagesPanel.vue'
import RemovePagesPanel from '../components/edit/RemovePagesPanel.vue'
import SetTextPanel from '../components/edit/SetTextPanel.vue'
import ResetTextPanel from '../components/edit/ResetTextPanel.vue'
import ViewChangesPanel from '../components/edit/ViewChangesPanel.vue'
import BranchTasksPanel from '../components/edit/BranchTasksPanel.vue'

const route = useRoute()
const router = useRouter()
const { user, hasRole } = useAuth()

const statusLabels = {
  in_work: 'В работе',
  in_review: 'Проверяется',
  in_accept: 'Завершение правок',
  accepted: 'Принято',
  rejected: 'Отклонено',
}
const statusColors = {
  in_work: 'blue',
  in_review: '#b39ddb',
  in_accept: 'teal',
  accepted: 'green',
  rejected: 'red',
}
const statusOptions = Object.entries(statusLabels).map(([value, title]) => ({ value, title }))

const branch = ref(null)
const loading = ref(true)
const error = ref(null)

const pageCount = ref(0)
const allowedExtensions = ref([])

const ACTIVE_VIEW_STORAGE_KEY = 'editView.activeView'
const VALID_VIEWS = ['add', 'remove', 'set_text', 'reset_text', 'view_changes']
const storedActiveView = localStorage.getItem(ACTIVE_VIEW_STORAGE_KEY)
const activeView = ref(VALID_VIEWS.includes(storedActiveView) ? storedActiveView : 'add')

watch(activeView, (value) => {
  localStorage.setItem(ACTIVE_VIEW_STORAGE_KEY, value)
})

const LOCKED_STATUSES = ['accepted', 'rejected', 'in_accept']

const statusLoading = ref(false)
const statusActionLoading = ref(false)
const confirmStatusDialog = ref(false)
const pendingStatus = ref(null)
const confirmReady = ref(false)
const CONFIRM_DELAY_MS = 2000
let confirmReadyTimer = null

const branchTasksRef = ref(null)
const galleryRef = ref(null)

const isAuthor = computed(() => !!(user.value && branch.value && user.value.id === branch.value.authorId))
const isLocked = computed(() => !!(branch.value && LOCKED_STATUSES.includes(branch.value.status)))

watch(isLocked, (locked) => {
  if (locked && activeView.value !== 'view_changes') {
    activeView.value = 'view_changes'
  }
})

let ws = null
let wsShouldReconnect = true

const loadBranch = async (id) => {
  try {
    const response = await http.get(`/api/documents/branches/${id}`)
    branch.value = {
      id: response.data.id,
      documentId: response.data.document_id,
      documentName: response.data.document_name,
      authorId: response.data.author_id,
      status: response.data.status,
      initialCommit: response.data.initial_commit,
      lastCommit: response.data.last_commit,
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

const requestSetStatus = (newStatus) => {
  if (!newStatus || newStatus === branch.value.status) return
  pendingStatus.value = newStatus
  confirmStatusDialog.value = true
  confirmReady.value = false
  clearTimeout(confirmReadyTimer)
  confirmReadyTimer = setTimeout(() => {
    confirmReady.value = true
  }, CONFIRM_DELAY_MS)
}

const cancelSetStatus = () => {
  clearTimeout(confirmReadyTimer)
  confirmStatusDialog.value = false
  pendingStatus.value = null
  confirmReady.value = false
}

const confirmSetStatus = async () => {
  const newStatus = pendingStatus.value
  statusLoading.value = true
  try {
    await http.post(`/api/documents/branches/${branch.value.id}/status`, { status: newStatus })
    branch.value.status = newStatus
    branchTasksRef.value.reload()
  } catch (err) {
    console.error('Ошибка при изменении статуса:', err)
  } finally {
    statusLoading.value = false
    confirmStatusDialog.value = false
    pendingStatus.value = null
    confirmReady.value = false
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
    loadBranch(branch.value.id)
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
  clearTimeout(confirmReadyTimer)
})
</script>

<style scoped>
.gallery-thumb {
  cursor: pointer;
}
.edit-view-menu-card {
  width: min-content;
}
.edit-view-menu :deep(.v-list-item) {
  min-height: unset;
  padding: 8px;
  overflow: visible;
}
.edit-view-menu :deep(.v-list-item__content) {
  overflow: visible;
  min-width: min-content;
}
.edit-view-menu :deep(.v-list-item__prepend) {
  margin-inline-end: 6px;
}
.edit-view-menu :deep(.v-list-item__prepend > .v-icon) {
  margin-inline-end: 0;
}
.edit-view-menu :deep(.v-list-item__spacer) {
  width: 6px;
}
.edit-view-menu-label {
  display: block;
  width: min-content;
  white-space: normal;
  overflow-wrap: normal;
  word-break: normal;
  line-height: 1.25;
}
</style>
