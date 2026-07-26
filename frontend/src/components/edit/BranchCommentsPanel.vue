<template>
  <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
    <h2 class="tw:font-serif tw:font-semibold tw:text-ink-900 tw:mb-4">Комментарии</h2>
    <div v-if="commentsError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mb-2">
      {{ commentsError }}
    </div>
    <div v-if="commentsLoading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
    <div v-else-if="!comments.length" class="tw:text-sm tw:text-gray-400 tw:mb-2">Комментариев пока нет</div>
    <ul v-else ref="commentsListRef" class="tw:space-y-2 tw:max-h-[600px] tw:overflow-y-auto tw:mb-4">
      <li v-for="comment in comments" :key="comment.id" class="tw:text-sm tw:text-gray-700">
        <template v-if="comment.type === 'branch_status'">
          {{ comment.author_display_name || 'Система' }}:<br>
          Изменил статус на
          <strong :style="{ color: statusColors[comment.text] || 'inherit' }">{{ statusLabels[comment.text] || comment.text }}</strong>
        </template>
        <template v-else-if="comment.type === 'branch_task'">
          {{ comment.author_display_name || 'Система' }}:<br>
          <em :style="{ color: taskStatusColors[comment.task_status] || 'inherit' }">{{ taskTypeLabels[comment.task_type] || comment.task_type }}</em>
        </template>
        <template v-else>
          {{ comment.author_display_name || 'Система' }}:<br>
          {{ comment.text }}
        </template>
      </li>
    </ul>

    <button
      type="button"
      class="tw:w-full tw:px-4 tw:py-2 tw:text-sm tw:text-gray-600 tw:border tw:border-gray-200 tw:rounded-lg tw:hover:bg-gray-50 tw:transition-colors"
      @click="openAddDialog"
    >
      Оставить комментарий
    </button>

    <AppModal v-model="addDialogOpen" max-width="tw:max-w-md">
      <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">Комментарий</h2>
      <textarea
        v-model="newCommentText"
        rows="4"
        placeholder="Текст комментария"
        class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"
      />
      <div v-if="submitError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
        {{ submitError }}
      </div>
      <div class="tw:flex tw:items-center tw:justify-end tw:gap-2 tw:mt-4">
        <button type="button" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors" @click="addDialogOpen = false">Отмена</button>
        <button
          type="button"
          :disabled="!newCommentText.trim() || submitting"
          class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
          @click="submitComment"
        >
          {{ submitting ? 'Отправка…' : 'Отправить' }}
        </button>
      </div>
    </AppModal>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import http from '../../api/http'
import AppModal from '../AppModal.vue'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
})

const statusLabels = {
  in_work: 'В работе',
  to_review: 'Отправлено на проверку',
  in_review: 'Проверяется',
  in_accept: 'Завершение правок',
  accepted: 'Принято',
  rejected: 'Отклонено',
}
const statusColors = {
  in_work: '#6b7280',
  to_review: '#2563eb',
  in_review: '#9333ea',
  in_accept: '#0d9488',
  accepted: '#16a34a',
  rejected: '#dc2626',
}

const taskTypeLabels = {
  create_repos: 'Создать документ',
  create_branch: 'Начать правки',
  insert_files: 'Добавить страницы',
  remove_files: 'Удалить страницы',
  text_from_image: 'Распознать текст',
  set_text: 'Задать текст',
  reset_text: 'Убрать текст',
  merge_branch: 'Завершить правки',
}
const taskStatusColors = {
  new: '#9ca3af',
  queued: '#9ca3af',
  running: '#2563eb',
  success: '#16a34a',
  error: '#dc2626',
}

const comments = ref([])
const commentsLoading = ref(true)
const commentsError = ref('')
const commentsListRef = ref(null)

const addDialogOpen = ref(false)
const newCommentText = ref('')
const submitting = ref(false)
const submitError = ref('')

const scrollToBottom = () => {
  nextTick(() => {
    const el = commentsListRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

const reload = async () => {
  commentsError.value = ''
  try {
    const response = await http.get(`/api/documents/branches/${props.branchId}/comments`)
    const hasNewComments = response.data.items.length > comments.value.length
    comments.value = response.data.items
    if (hasNewComments) scrollToBottom()
  } catch (err) {
    const status = err.response ? err.response.status : null
    commentsError.value = status
      ? `Не удалось получить комментарии (код ${status}).`
      : 'Не удалось получить комментарии.'
    console.error('Ошибка при получении комментариев ветки:', err)
  } finally {
    commentsLoading.value = false
  }
}

function openAddDialog() {
  newCommentText.value = ''
  submitError.value = ''
  addDialogOpen.value = true
}

async function submitComment() {
  const text = newCommentText.value.trim()
  if (!text) return
  submitting.value = true
  submitError.value = ''
  try {
    await http.post(`/api/documents/branches/${props.branchId}/comments`, { text })
    addDialogOpen.value = false
    await reload()
  } catch (err) {
    submitError.value = 'Не удалось отправить комментарий.'
    console.error('Ошибка при отправке комментария:', err)
  } finally {
    submitting.value = false
  }
}

onMounted(reload)

defineExpose({ reload })
</script>
