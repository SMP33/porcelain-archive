<template>
  <v-layout>
    <AppToolbar />
    <v-main>
      <v-container fluid>
        <v-row>
          <v-col :cols="selectedTask ? 4 : 12">
            <v-card>
              <v-card-title>Задачи</v-card-title>
              <v-card-text>
                <v-data-table-server
                  v-model:page="page"
                  v-model:items-per-page="itemsPerPage"
                  :headers="headers"
                  :items-length="totalItems"
                  :items="serverItems"
                  :loading="loading"
                  :items-per-page-options="[
                    { value: 25, title: '25' },
                    { value: 50, title: '50' },
                    { value: 100, title: '100' },
                    { value: 500, title: '500' },
                  ]"
                  class="elevation-1"
                  item-value="id"
                  @update:options="loadItems"
                  @click:row="selectTask"
                >
                  <template v-slot:item.type="{ item }">{{ taskTypeLabel(item.type) }}</template>
                  <template v-slot:item.author_display_name="{ item }">{{ item.author_display_name || '—' }}</template>
                  <template v-slot:item.status="{ item }">
                    <v-chip :color="statusColor(item.status)" size="small" label>{{ statusLabel(item.status) }}</v-chip>
                  </template>
                </v-data-table-server>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col v-if="selectedTask" cols="8">
            <v-card>
              <v-card-title class="d-flex justify-space-between align-center">
                <span>Данные задачи №{{ selectedTask.id }}</span>
                <v-btn icon variant="text" @click="selectedTask = null">
                  <v-icon>mdi-close</v-icon>
                </v-btn>
              </v-card-title>
              <v-card-text>
                <pre class="text-body-2">{{ JSON.stringify(selectedTask.data, null, 2) }}</pre>

                <v-divider class="my-4"></v-divider>

                <div class="text-subtitle-2 mb-2">Лог</div>
                <v-progress-circular v-if="taskLogLoading" indeterminate size="20"></v-progress-circular>
                <div v-else class="log-scroll-area">
                  <pre class="log-text">{{ taskLog || "Лог пуст" }}</pre>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-layout>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import http from '../api/http'
import AppToolbar from '../components/AppToolbar.vue'

const page = ref(1)
const itemsPerPage = ref(25)
const headers = ref([
  { title: 'ID', align: 'start', sortable: false, key: 'id' },
  { title: 'Тип', key: 'type', align: 'end' },
  { title: 'Автор', key: 'author_display_name', align: 'end' },
  { title: 'Статус', key: 'status', align: 'end' },
])

const serverItems = ref([])
const loading = ref(true)
const totalItems = ref(0)
const selectedTask = ref(null)
const taskLog = ref('')
const taskLogLoading = ref(false)

const statusColor = (status) => {
  switch (status) {
    case 'success': return 'green'
    case 'error': return 'red'
    case 'running': return 'blue'
    case 'queued':
    case 'new':
    default: return 'grey'
  }
}

const TASK_TYPE_LABELS = {
  create_repos: 'Создать документ',
  create_branch: 'Начать правки',
  insert_files: 'Добавить страницы',
  remove_files: 'Удалить страницы',
  set_text: 'Задать текст',
  reset_text: 'Убрать текст',
  merge_branch: 'Завершить правки',
}
const taskTypeLabel = (type) => TASK_TYPE_LABELS[type] || type

const STATUS_LABELS = {
  new: 'Создается',
  queued: 'Ожидает',
  running: 'В процессе',
  success: 'Готово',
  error: 'Ошибка',
}
const statusLabel = (status) => STATUS_LABELS[status] || status

let lastTableOptions = { page: 1, itemsPerPage: itemsPerPage.value }
let hasAutoSelected = false
let ws = null
let wsShouldReconnect = true

const loadItems = async (options) => {
  lastTableOptions = options
  const { page, itemsPerPage } = options
  loading.value = true
  try {
    const offset = (page - 1) * itemsPerPage
    const response = await http.get('/api/tasks/', {
      params: { offset, limit: itemsPerPage },
    })
    serverItems.value = response.data.items
    totalItems.value = response.data.total

    if (!hasAutoSelected && serverItems.value.length) {
      hasAutoSelected = true
      await selectTask(null, { item: serverItems.value[0] })
    }
  } catch (error) {
    console.error('Ошибка при загрузке задач:', error)
  } finally {
    loading.value = false
  }
}

const refreshSelectedTaskLog = async () => {
  if (!selectedTask.value) return
  try {
    const response = await http.get(`/api/tasks/${selectedTask.value.id}/log`)
    taskLog.value = response.data.log
  } catch (error) {
    console.error('Ошибка при обновлении лога задачи:', error)
  }
}

const connectTaskUpdates = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${window.location.host}/api/tasks/ws`)

  ws.onmessage = async () => {
    const previousTotal = totalItems.value
    await loadItems(lastTableOptions)

    if (totalItems.value > previousTotal) {
      // Появилась новая задача - переключаемся на неё
      page.value = 1
      await loadItems({ ...lastTableOptions, page: 1 })
      selectedTask.value = serverItems.value[0]
      await refreshSelectedTaskLog()
      return
    }

    if (selectedTask.value) {
      const updated = serverItems.value.find((task) => task.id === selectedTask.value.id)
      if (updated) {
        selectedTask.value = updated
      }
      await refreshSelectedTaskLog()
    }
  }

  ws.onclose = () => {
    if (wsShouldReconnect) {
      setTimeout(connectTaskUpdates, 2000)
    }
  }
}

const selectTask = async (event, { item }) => {
  selectedTask.value = item
  taskLog.value = ''
  taskLogLoading.value = true
  try {
    const response = await http.get(`/api/tasks/${item.id}/log`)
    taskLog.value = response.data.log
  } catch (error) {
    console.error('Ошибка при загрузке лога задачи:', error)
  } finally {
    taskLogLoading.value = false
  }
}

onMounted(connectTaskUpdates)

onUnmounted(() => {
  wsShouldReconnect = false
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.log-scroll-area {
  max-height: 500px;
  overflow-y: auto;
  background-color: #333;
  border-radius: 4px;
}
.log-text {
  margin: 0;
  padding: 12px;
  color: #fff;
  background-color: #333;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
