<template>
  <v-layout class="d-flex align-center justify-center" style="min-height: 100vh;">
    <v-card width="400" class="pa-4">
      <v-card-title class="text-center">Авторизация</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="handleLogin">
          <v-text-field
            v-model="username"
            label="Логин"
            prepend-inner-icon="mdi-account"
            required
          ></v-text-field>
          <v-text-field
            v-model="password"
            label="Пароль"
            type="password"
            prepend-inner-icon="mdi-lock"
            required
          ></v-text-field>
          <v-alert v-if="error" type="error" density="compact" class="mb-4">{{ error }}</v-alert>
          <v-btn type="submit" color="primary" block :loading="loading">Войти</v-btn>
        </v-form>
      </v-card-text>
    </v-card>
  </v-layout>
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
