<template>
  <div>
    <main>
      <div class="tw:mb-4">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">Администрирование</h1>
      </div>
      <div>
        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
          <button
            type="button"
            :disabled="backupLoading"
            class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
            @click="handleBackup"
          >
            {{ backupLoading ? 'Запуск…' : 'Сделать бэкап' }}
          </button>
          <div v-if="backupMessage" class="tw:mt-4 tw:text-sm" :class="backupError ? 'tw:text-red-600' : 'tw:text-green-600'">
            {{ backupMessage }}
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '../ceramic/api/http'
import { inject } from 'vue'
import { useAuth } from '../ceramic/composables/useAuth'

inject('adminHeading').value = 'Обслуживание'

const router = useRouter()
const { hasRole } = useAuth()

const backupLoading = ref(false)
const backupMessage = ref('')
const backupError = ref(false)

async function handleBackup() {
  backupLoading.value = true
  backupMessage.value = ''
  backupError.value = false
  try {
    await http.post('/api/tasks/backup', {})
    backupMessage.value = 'Задача бэкапа создана. Ход выполнения можно отследить в списке задач.'
  } catch (error) {
    const status = error.response ? error.response.status : null
    backupError.value = true
    backupMessage.value = status
      ? `Не удалось запустить бэкап (код ${status}).`
      : 'Не удалось запустить бэкап.'
    console.error('Ошибка при запуске бэкапа:', error)
  } finally {
    backupLoading.value = false
  }
}

onMounted(() => {
  if (!hasRole('admin')) {
    router.push('/admin/access-denied')
  }
})
</script>
