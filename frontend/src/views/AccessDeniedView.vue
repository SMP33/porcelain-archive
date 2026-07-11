<template>
  <v-layout>
    <AppToolbar />
    <v-main>
      <v-container>
        <v-card>
          <v-card-title>Страница недоступна</v-card-title>
          <v-card-text>
            <v-alert type="warning" density="compact">
              У вас недостаточно прав для просмотра этой страницы, либо она не существует.
            </v-alert>
          </v-card-text>
          <v-card-actions>
            <v-btn color="primary" to="/">На главную</v-btn>
            <v-btn v-if="!user" color="secondary" to="/login">Войти</v-btn>
          </v-card-actions>
        </v-card>
      </v-container>
    </v-main>
  </v-layout>
</template>

<script setup>
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'

const { user } = useAuth()
</script>
