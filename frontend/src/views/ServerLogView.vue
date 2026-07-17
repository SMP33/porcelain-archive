<template>
  <div class="tw:min-h-screen tw:bg-gray-100">
    <AppToolbar />
    <main class="tw:md:pl-[232px]">
      <div class="tw:border-b tw:border-gray-200 tw:bg-white tw:px-8 tw:py-4 tw:flex tw:items-center tw:justify-between">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">Лог сервера</h1>
        <button
          type="button"
          :disabled="serverLogLoading"
          class="tw:p-2 tw:text-gray-500 tw:hover:text-clay-500 tw:transition-colors tw:disabled:opacity-50"
          @click="fetchServerLog"
        >
          <i class="mdi mdi-refresh tw:text-xl" :class="{ 'tw:animate-spin': serverLogLoading }" />
        </button>
      </div>
      <div class="tw:px-8 tw:py-6">
        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
          <div v-if="serverLogLoading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
          <div v-else class="tw:max-h-[70vh] tw:overflow-y-auto tw:bg-ink-800 tw:rounded-lg">
            <pre class="tw:m-0 tw:p-3 tw:text-white tw:text-xs tw:whitespace-pre-wrap tw:break-words">{{ serverLog || 'Лог пуст' }}</pre>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'

const router = useRouter()
const route = useRoute()
const { hasRole } = useAuth()

const serverLog = ref('')
const serverLogLoading = ref(false)

const fetchServerLog = async () => {
  serverLogLoading.value = true
  try {
    const response = await http.get('/api/tasks/server-log')
    serverLog.value = response.data.log
  } catch (error) {
    const status = error.response ? error.response.status : null
    if (status === 401) {
      router.push({ name: 'login', query: { redirect: route.fullPath } })
      return
    }
    if (status === 403) {
      router.push('/access-denied')
      return
    }
    console.error('Ошибка при загрузке лога сервера:', error)
  } finally {
    serverLogLoading.value = false
  }
}

onMounted(() => {
  if (!hasRole('admin')) {
    router.push('/access-denied')
    return
  }
  fetchServerLog()
})
</script>
