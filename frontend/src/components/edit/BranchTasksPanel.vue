<template>
  <v-card>
    <v-card-title class="text-subtitle-1">Задачи по этому набору изменений</v-card-title>
    <v-card-text>
      <v-alert v-if="tasksError" type="error" density="compact" class="mb-2">{{ tasksError }}</v-alert>
      <v-data-table
        :headers="taskHeaders"
        :items="branchTasks"
        :loading="tasksLoading"
        density="compact"
        no-data-text="Задач пока нет"
        items-per-page="-1"
        hide-default-footer
      >
        <template v-slot:item.type="{ item }">{{ taskTypeLabel(item.type) }}</template>
        <template v-slot:item.status="{ item }">
          <v-chip :color="statusColor(item.status)" size="small" label>{{ statusLabel(item.status) }}</v-chip>
        </template>
      </v-data-table>
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
const taskHeaders = ref([
  { title: 'ID', align: 'start', sortable: false, key: 'id' },
  { title: 'Тип', key: 'type', align: 'end' },
  { title: 'Статус', key: 'status', align: 'end' },
])

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

const reload = async () => {
  tasksError.value = ''
  try {
    const response = await http.get(`/api/tasks/branch/${props.branchId}`)
    branchTasks.value = response.data.items
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
