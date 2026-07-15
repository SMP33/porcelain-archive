<template>
  <v-layout full-height>
    <AppToolbar />
    <v-main scrollable>
      <v-container>
        <v-card>
          <v-card-title class="d-flex justify-space-between align-center">
            <span>Лог сервера</span>
            <v-btn icon variant="text" :loading="serverLogLoading" @click="fetchServerLog">
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-progress-circular v-if="serverLogLoading" indeterminate size="20"></v-progress-circular>
            <div v-else class="log-scroll-area">
              <pre class="log-text">{{ serverLog || "Лог пуст" }}</pre>
            </div>
          </v-card-text>
        </v-card>
      </v-container>
    </v-main>
  </v-layout>
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

<style scoped>
.log-scroll-area {
  max-height: 70vh;
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
