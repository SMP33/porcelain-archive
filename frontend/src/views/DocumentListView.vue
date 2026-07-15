<template>
  <v-layout full-height>
    <AppToolbar />
    <v-main scrollable>
      <v-container>
        <v-card>
          <v-card-title class="d-flex justify-space-between align-center">
            <span>Документы</span>
            <v-btn v-if="user" color="primary" @click="showCreateDialog = true">Добавить документ</v-btn>
          </v-card-title>
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
              item-value="name"
              @update:options="loadItems"
              @click:row="openDocument"
            ></v-data-table-server>
          </v-card-text>
        </v-card>
      </v-container>
    </v-main>

    <v-dialog v-model="showCreateDialog" max-width="500">
      <v-card>
        <v-card-title>Новый документ</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newDocumentName"
            label="Название документа"
            autofocus
            @keyup.enter="handleCreateDocument"
          ></v-text-field>
          <v-alert v-if="createError" type="error" density="compact">{{ createError }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showCreateDialog = false">Отмена</v-btn>
          <v-btn color="primary" :loading="creating" @click="handleCreateDocument">Создать</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'

const router = useRouter()
const { user } = useAuth()

const itemsPerPage = ref(25)
const headers = ref([
  { title: 'ID', align: 'start', sortable: false, key: 'id' },
  { title: 'Название документа', key: 'name', align: 'end' },
])

const serverItems = ref([])
const loading = ref(true)
const totalItems = ref(0)

const showCreateDialog = ref(false)
const newDocumentName = ref('')
const creating = ref(false)
const createError = ref('')

const loadItems = async ({ page, itemsPerPage }) => {
  loading.value = true
  try {
    const offset = (page - 1) * itemsPerPage
    const response = await http.get('/api/documents/', {
      params: { offset, limit: itemsPerPage },
    })
    serverItems.value = response.data.items
    totalItems.value = response.data.total
  } catch (error) {
    console.error('Ошибка при загрузке документов:', error)
  } finally {
    loading.value = false
  }
}

const openDocument = (event, { item }) => {
  router.push(`/document/${item.id}`)
}

const handleCreateDocument = async () => {
  if (!newDocumentName.value) {
    return
  }
  creating.value = true
  createError.value = ''
  try {
    const response = await http.post('/api/documents/create', { name: newDocumentName.value })
    router.push(`/document/${response.data.id}`)
  } catch (error) {
    createError.value = 'Не удалось создать документ.'
    console.error('Ошибка при создании документа:', error)
  } finally {
    creating.value = false
  }
}
</script>
