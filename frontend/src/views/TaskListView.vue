<template>
  <div class="tw:min-h-screen tw:bg-gray-100">
    <AppToolbar />
    <main class="tw:md:pl-[232px]">
      <div class="tw:border-b tw:border-gray-200 tw:bg-white tw:px-8 tw:py-4">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">Задачи</h1>
      </div>
      <div class="tw:px-8 tw:py-6">
        <div class="tw:grid tw:grid-cols-1" :class="selectedTask ? 'tw:lg:grid-cols-12 tw:gap-4' : ''">
          <div :class="selectedTask ? 'tw:lg:col-span-4' : ''" class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
            <div class="tw:overflow-x-auto">
              <table class="tw:w-full tw:text-sm">
                <tbody class="tw:divide-y tw:divide-gray-100">
                  <tr
                    v-for="item in items"
                    :key="item.id"
                    class="tw:cursor-pointer tw:transition-colors"
                    :class="selectedTask && selectedTask.id === item.id ? 'tw:bg-clay-50' : 'tw:hover:bg-clay-50/60'"
                    @click="selectTask(item)"
                  >
                    <td class="tw:pl-4 tw:py-3 tw:w-10">
                      <i :class="taskTypeIcon(item.type)" class="mdi tw:text-lg" :style="{ color: statusColor(item.status) }" />
                    </td>
                    <td class="tw:py-3">
                      <div class="tw:text-gray-800">№{{ item.id }} {{ taskTypeLabel(item.type) }}</div>
                      <div class="tw:text-xs tw:text-gray-400">{{ item.author_display_name || '—' }}</div>
                    </td>
                    <td class="tw:pr-4 tw:py-3 tw:w-10 tw:text-right">
                      <i :class="statusIcon(item.status)" class="mdi tw:text-lg" :style="{ color: statusColor(item.status) }" />
                    </td>
                  </tr>
                  <tr v-if="!loading && !items.length">
                    <td colspan="3" class="tw:px-4 tw:py-8 tw:text-center tw:text-gray-400">Нет данных</td>
                  </tr>
                  <tr v-if="loading">
                    <td colspan="3" class="tw:px-4 tw:py-8 tw:text-center tw:text-gray-400">Загрузка…</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="tw:px-4 tw:pb-4">
              <AppPager
                :page="page"
                :page-count="pageCount"
                :items-per-page="itemsPerPage"
                :items-per-page-options="[25, 50, 100, 500]"
                :total="total"
                @update:page="goToPage"
                @update:items-per-page="setItemsPerPage"
              />
            </div>
          </div>

          <div v-if="selectedTask" class="tw:lg:col-span-8 tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
            <div class="tw:flex tw:items-center tw:justify-between tw:mb-4">
              <span class="tw:font-serif tw:font-semibold tw:text-ink-900">Данные задачи №{{ selectedTask.id }}</span>
              <button type="button" class="tw:p-1 tw:text-gray-400 tw:hover:text-gray-600 tw:transition-colors" @click="selectedTask = null">
                <i class="mdi mdi-close tw:text-lg" />
              </button>
            </div>
            <pre class="tw:text-xs tw:text-gray-700 tw:whitespace-pre-wrap tw:break-words">{{ JSON.stringify(selectedTask.data, null, 2) }}</pre>

            <div class="tw:my-4 tw:border-t tw:border-gray-100" />

            <div class="tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-2">Лог</div>
            <div v-if="taskLogLoading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
            <div v-else class="tw:max-h-[500px] tw:overflow-y-auto tw:bg-ink-800 tw:rounded-lg">
              <pre class="tw:m-0 tw:p-3 tw:text-white tw:text-xs tw:whitespace-pre-wrap tw:break-words">{{ taskLog || 'Лог пуст' }}</pre>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import http from '../api/http'
import AppToolbar from '../components/AppToolbar.vue'
import AppPager from '../components/AppPager.vue'
import { usePagedTable } from '../composables/usePagedTable'

const { page, itemsPerPage, items, total, loading, pageCount, reload, goToPage, setItemsPerPage } = usePagedTable(
  async ({ offset, limit }) => {
    const response = await http.get('/api/tasks/', { params: { offset, limit } })
    return { items: response.data.items, total: response.data.total }
  },
)

const selectedTask = ref(null)
const taskLog = ref('')
const taskLogLoading = ref(false)

const statusColor = (status) => {
  switch (status) {
    case 'success': return '#16a34a'
    case 'error': return '#dc2626'
    case 'running': return '#2563eb'
    case 'queued':
    case 'new':
    default: return '#9ca3af'
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

const TASK_TYPE_ICONS = {
  create_repos: 'mdi-file-document-plus-outline',
  create_branch: 'mdi-source-branch-plus',
  insert_files: 'mdi-file-plus',
  remove_files: 'mdi-file-remove',
  set_text: 'mdi-file-pdf-box',
  reset_text: 'mdi-text-box-remove',
  merge_branch: 'mdi-source-merge',
}
const taskTypeIcon = (type) => TASK_TYPE_ICONS[type] || 'mdi-cog'

const STATUS_ICONS = {
  new: 'mdi-clock-outline',
  queued: 'mdi-clock-outline',
  running: 'mdi-progress-clock',
  success: 'mdi-check-circle',
  error: 'mdi-alert-circle',
}
const statusIcon = (status) => STATUS_ICONS[status] || 'mdi-help-circle'

let hasAutoSelected = false
let ws = null
let wsShouldReconnect = true

async function refreshSelectedTaskLog() {
  if (!selectedTask.value) return
  try {
    const response = await http.get(`/api/tasks/${selectedTask.value.id}/log`)
    taskLog.value = response.data.log
  } catch (error) {
    console.error('Ошибка при обновлении лога задачи:', error)
  }
}

async function selectTask(item) {
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

async function loadItemsAndAutoSelect() {
  await reload()
  if (!hasAutoSelected && items.value.length) {
    hasAutoSelected = true
    await selectTask(items.value[0])
  }
}

function connectTaskUpdates() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${window.location.host}/api/tasks/ws`)

  ws.onmessage = async () => {
    const previousTotal = total.value
    await reload()

    if (total.value > previousTotal) {
      // Появилась новая задача - переключаемся на неё
      page.value = 1
      await reload()
      selectedTask.value = items.value[0]
      await refreshSelectedTaskLog()
      return
    }

    if (selectedTask.value) {
      const updated = items.value.find((task) => task.id === selectedTask.value.id)
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

onMounted(() => {
  loadItemsAndAutoSelect()
  connectTaskUpdates()
})

onUnmounted(() => {
  wsShouldReconnect = false
  if (ws) {
    ws.close()
  }
})
</script>
