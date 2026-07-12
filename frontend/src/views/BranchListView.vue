<template>
  <v-layout>
    <AppToolbar />
    <v-main>
      <v-container>
        <v-card>
          <v-card-title>Наборы изменений</v-card-title>
          <v-card-text>
            <v-data-table-server
              v-model:items-per-page="itemsPerPage"
              :headers="headers"
              :items-length="totalItems"
              :items="serverItems"
              :loading="loading"
              :items-per-page-options="[
                { value: 25, title: '25' },
                { value: 50, title: '50' },
                { value: 100, title: '100' },
                { value: 500, title: '500' },
              ]"
              class="elevation-1"
              item-value="id"
              @update:options="loadItems"
              @click:row="openBranch"
            >
              <template v-slot:item.status="{ item }">
                <v-chip :color="statusColors[item.status] || 'grey'" size="small">
                  {{ statusLabels[item.status] || item.status }}
                </v-chip>
              </template>
            </v-data-table-server>
          </v-card-text>
        </v-card>
      </v-container>
    </v-main>
  </v-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '../api/http'
import AppToolbar from '../components/AppToolbar.vue'

const router = useRouter()

const statusLabels = {
  in_work: 'В работе',
  in_review: 'Проверяется',
  accepted: 'Принято',
  rejected: 'Отклонено',
}
const statusColors = {
  in_work: 'blue',
  in_review: '#b39ddb',
  accepted: 'green',
  rejected: 'red',
}

const itemsPerPage = ref(25)
const headers = ref([
  { title: 'ID', align: 'start', sortable: false, key: 'id' },
  { title: 'Название', key: 'document_name', align: 'end' },
  { title: 'Автор', key: 'author_name', align: 'end' },
  { title: 'Дата создания', key: 'created_at', align: 'end' },
  { title: 'Дата последнего изменения', key: 'last_change_at', align: 'end' },
  { title: 'Статус', key: 'status', align: 'end', sortable: false },
])

const serverItems = ref([])
const loading = ref(true)
const totalItems = ref(0)

const loadItems = async ({ page, itemsPerPage }) => {
  loading.value = true
  try {
    const offset = (page - 1) * itemsPerPage
    const response = await http.get('/api/documents/branches/', {
      params: { offset, limit: itemsPerPage },
    })
    serverItems.value = response.data.items
    totalItems.value = response.data.total
  } catch (error) {
    console.error('Ошибка при загрузке наборов изменений:', error)
  } finally {
    loading.value = false
  }
}

const openBranch = (event, { item }) => {
  router.push(`/edit/${item.id}`)
}
</script>
