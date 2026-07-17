<template>
  <div class="tw:bg-gray-100 tw:min-h-screen tw:flex tw:flex-col tw:items-center tw:justify-center tw:p-4">
    <div class="tw:flex tw:items-center tw:gap-3 tw:mb-6">
      <span class="tw:flex tw:items-center tw:justify-center tw:w-9 tw:h-9 tw:shrink-0 tw:rounded tw:bg-clay-500" style="transform: skewX(-10deg);">
        <i class="mdi mdi-book-open-page-variant tw:text-white tw:text-xl" style="transform: skewX(10deg); display: inline-block;" />
      </span>
      <span class="tw:font-serif tw:font-bold tw:text-xl tw:text-ink-800">Архив</span>
    </div>

    <div class="tw:bg-white tw:rounded-xl tw:shadow-md tw:p-8 tw:w-full tw:max-w-sm">
      <h1 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:text-center tw:mb-6">Авторизация</h1>
      <form class="tw:space-y-4" @submit.prevent="handleLogin">
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Логин</label>
          <input
            v-model="username"
            type="text"
            required
            class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"
          >
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Пароль</label>
          <input
            v-model="password"
            type="password"
            required
            class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"
          >
        </div>
        <div v-if="error" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2">
          {{ error }}
        </div>
        <button
          type="submit"
          :disabled="loading"
          class="tw:w-full tw:px-5 tw:py-2.5 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
        >
          {{ loading ? 'Вход…' : 'Войти' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const route = useRoute()
const { checkAuth } = useAuth()

const username = ref('admin')
const password = ref('admin')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    // FastAPI ожидает данные в формате `application/x-www-form-urlencoded`
    const params = new URLSearchParams()
    params.append('username', username.value)
    params.append('password', password.value)

    await http.post('/api/users/login', params)
    await checkAuth()
    router.push(route.query.redirect || '/')
  } catch (err) {
    error.value = 'Неверный логин или пароль.'
    console.error('Ошибка входа:', err)
  } finally {
    loading.value = false
  }
}
</script>
