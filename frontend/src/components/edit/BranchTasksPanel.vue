<template>
  <v-card>
    <v-card-title class="text-subtitle-1">История</v-card-title>
    <v-card-text>
      <v-alert v-if="tasksError" type="error" density="compact" class="mb-2">{{ tasksError }}</v-alert>
      <v-progress-circular v-if="tasksLoading" indeterminate size="20"></v-progress-circular>
      <div v-else-if="!branchTasks.length" class="text-medium-emphasis">Задач пока нет</div>
      <div v-else class="task-list">
        <v-tooltip v-for="task in branchTasks" :key="task.id" location="top">
          <template v-slot:activator="{ props }">
            <div v-bind="props" class="task-list-item">
              <v-icon :color="statusColor(task.status)" size="22">{{ taskTypeIcon(task.type) }}</v-icon>
              <span class="task-list-item-id text-medium-emphasis">{{ task.id }}</span>
            </div>
          </template>
          <div>№{{ task.id }} · {{ taskTypeLabel(task.type) }}</div>
          <div>{{ task.author_display_name || '—' }}</div>
          <div>{{ statusLabel(task.status) }}</div>
        </v-tooltip>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import http from '../../api/http'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
})

const branchTasks = ref([])
const tasksLoading = ref(true)
const tasksError = ref('')

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

<style scoped>
.task-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 600px;
  overflow-y: auto;
}
.task-list-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 44px;
  cursor: default;
}
.task-list-item-id {
  font-size: 11px;
  line-height: 1.2;
  margin-top: 2px;
}
</style>
