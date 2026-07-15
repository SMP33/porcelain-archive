<template>
  <v-layout full-height>
    <AppToolbar />
    <v-main scrollable>
      <v-container>
        <v-card>
          <v-card-title>Страница не найдена</v-card-title>
          <v-card-text>
            <v-alert type="warning" density="compact">Такой страницы не существует.</v-alert>
          </v-card-text>
          <v-card-actions>
            <v-btn color="primary" to="/">На главную</v-btn>
          </v-card-actions>
        </v-card>
      </v-container>
    </v-main>
  </v-layout>
</template>

<script setup>
import AppToolbar from '../components/AppToolbar.vue'
</script>
