<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth'
import teapotIcon from '../../assets/img/teapot-icon.png'

const route = useRoute()
const router = useRouter()
const { login } = useAuth()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  loading.value = true
  error.value = ''
  try {
    await login(username.value, password.value)
    router.push(route.query.redirect || '/ceramic/admin')
  } catch (e) {
    if (e.response?.status === 429) {
      error.value = 'Слишком много попыток входа. Попробуйте позже.'
    } else {
      error.value = 'Неверное имя пользователя или пароль'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="ceramic-reset tw:bg-gray-100 tw:min-h-screen tw:flex tw:items-center tw:justify-center">
    <div class="tw:bg-white tw:rounded-xl tw:shadow-md tw:p-8 tw:w-full tw:max-w-sm">
      <div class="tw:text-center tw:mb-6">
        <img :src="teapotIcon" alt="" class="tw:w-12 tw:h-12 tw:object-contain tw:mx-auto tw:mb-2">
        <h1 class="tw:text-xl tw:font-semibold tw:text-gray-800">Вход в админку</h1>
      </div>
      <div v-if="error" class="tw:mb-4 tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-4 tw:py-2">
        {{ error }}
      </div>
      <form @submit.prevent="onSubmit">
        <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Имя пользователя</label>
        <input v-model="username" type="text" autofocus required autocomplete="username"
               class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:mb-4 tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
        <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Пароль</label>
        <input v-model="password" type="password" required autocomplete="current-password"
               class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:mb-4 tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
        <button type="submit" :disabled="loading"
                class="tw:w-full tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
          Войти
        </button>
      </form>
    </div>
  </div>
</template>
