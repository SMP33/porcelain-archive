<template>
  <v-card>
    <v-card-title class="d-flex justify-space-between align-center">
      <span class="text-subtitle-1">Операции</span>
      <v-btn
        icon
        variant="text"
        size="small"
        :title="collapsed ? 'Развернуть' : 'Свернуть'"
        @click="$emit('update:collapsed', !collapsed)"
      >
        <v-icon>{{ collapsed ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text>
      <v-alert v-if="tasksError" type="error" density="compact" class="mb-2">{{ tasksError }}</v-alert>
      <v-data-table
        :headers="visibleTaskHeaders"
        :items="branchTasks"
        :loading="tasksLoading"
        density="compact"
        no-data-text="Задач пока нет"
        items-per-page="-1"
        hide-default-footer
        :class="{ 'collapsed-table': collapsed }"
      >
        <template v-slot:item.type="{ item }">{{ taskTypeLabel(item.type) }}</template>
        <template v-slot:item.author_display_name="{ item }">{{ item.author_display_name || '—' }}</template>
        <template v-slot:item.status="{ item }">
          <v-chip :color="statusColor(item.status)" size="small" label>{{ statusLabel(item.status) }}</v-chip>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import http from '../../api/http'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
  collapsed: { type: Boolean, default: false },
})

defineEmits(['update:collapsed'])

const branchTasks = ref([])
const tasksLoading = ref(true)
const tasksError = ref('')
const taskHeaders = ref([
  { title: 'ID', align: 'start', sortable: false, key: 'id' },
  { title: 'Тип', key: 'type', align: 'end' },
  { title: 'Автор', key: 'author_display_name', align: 'end' },
  { title: 'Статус', key: 'status', align: 'end' },
])
const collapsedTaskHeaders = [
  { title: 'ID', align: 'start', sortable: false, key: 'id', width: '48px' },
  { title: 'Статус', key: 'status', align: 'start', sortable: false, width: '110px' },
]

const visibleTaskHeaders = computed(() => (props.collapsed ? collapsedTaskHeaders : taskHeaders.value))

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

<style scoped>
.collapsed-table {
  width: auto;
}

.collapsed-table :deep(th),
.collapsed-table :deep(td) {
  padding: 0 8px;
}
</style>
