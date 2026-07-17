<template>
  <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
    <h2 class="tw:font-serif tw:font-semibold tw:text-ink-900 tw:mb-4">История</h2>
    <div v-if="tasksError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mb-2">
      {{ tasksError }}
    </div>
    <div v-if="tasksLoading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
    <div v-else-if="!branchTasks.length" class="tw:text-sm tw:text-gray-400">Задач пока нет</div>
    <div v-else class="tw:flex tw:flex-wrap tw:gap-2 tw:max-h-[600px] tw:overflow-y-auto">
      <AppTooltip v-for="task in branchTasks" :key="task.id">
        <div class="tw:flex tw:flex-col tw:items-center tw:w-11 tw:cursor-default">
          <i :class="taskTypeIcon(task.type)" class="mdi tw:text-xl" :style="{ color: statusColor(task.status) }" />
          <span class="tw:text-[11px] tw:leading-tight tw:text-gray-400 tw:mt-0.5">{{ task.id }}</span>
        </div>
        <template #content>
          <div>№{{ task.id }} · {{ taskTypeLabel(task.type) }}</div>
          <div>{{ task.author_display_name || '—' }}</div>
          <div>{{ statusLabel(task.status) }}</div>
        </template>
      </AppTooltip>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import http from '../../api/http'
import AppTooltip from '../AppTooltip.vue'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
})

const branchTasks = ref([])
const tasksLoading = ref(true)
const tasksError = ref('')

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

const STATUS_LABELS = {
  new: 'Создается',
  queued: 'Ожидает',
  running: 'В процессе',
  success: 'Готово',
  error: 'Ошибка',
}
const statusLabel = (status) => STATUS_LABELS[status] || status

const reload = async () => {
  tasksError.value = ''
  try {
    const response = await http.get(`/api/tasks/branch/${props.branchId}`)
    branchTasks.value = [...response.data.items].sort((a, b) => a.id - b.id)
  } catch (err) {
    const status = err.response ? err.response.status : null
    tasksError.value = status
      ? `Не удалось получить задачи набора изменений (код ${status}).`
      : 'Не удалось получить задачи набора изменений.'
    console.error('Ошибка при получении задач ветки:', err)
  } finally {
    tasksLoading.value = false
  }
}

onMounted(reload)

defineExpose({ reload })
</script>
