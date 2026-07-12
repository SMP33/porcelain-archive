<template>
  <v-layout>
    <AppToolbar />
    <v-main>
      <v-container>
        <v-card>
          <v-card-title class="d-flex justify-space-between align-center">
            <span>Пользователи</span>
            <v-btn v-if="hasRole('admin')" color="primary" @click="showCreateUserDialog = true">Создать пользователя</v-btn>
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
              item-value="id"
              @update:options="loadItems"
            >
              <template v-slot:item.role="{ item }">
                {{ roleLabels[item.role] || item.role }}
              </template>
            </v-data-table-server>
          </v-card-text>
        </v-card>
      </v-container>
    </v-main>

    <v-dialog v-model="showCreateUserDialog" max-width="500">
      <v-card>
        <v-card-title>Новый пользователь</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newUser.username"
            label="Логин"
            autofocus
          ></v-text-field>
          <v-text-field
            v-model="newUser.password"
            label="Пароль"
            type="password"
          ></v-text-field>
          <v-text-field
            v-model="newUser.display_name"
            label="ФИО"
          ></v-text-field>
          <v-text-field
            v-model="newUser.email"
            label="Email"
          ></v-text-field>
          <v-select
            v-model="newUser.role"
            label="Роль"
            :items="roleOptions"
            item-title="title"
            item-value="value"
          ></v-select>
          <v-alert v-if="createUserError" type="error" density="compact" class="mt-2">{{ createUserError }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showCreateUserDialog = false">Отмена</v-btn>
          <v-btn color="primary" :loading="creatingUser" @click="handleCreateUser">Создать</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-layout>
</template>

<script setup>
import { ref } from 'vue'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'

const { hasRole } = useAuth()

const roleLabels = {
  user: 'Пользователь',
  moderator: 'Модератор',
  admin: 'Администратор',
}
const roleOptions = [
  { title: 'Пользователь', value: 'user' },
  { title: 'Модератор', value: 'moderator' },
  { title: 'Администратор', value: 'admin' },
]

const itemsPerPage = ref(25)
const headers = ref([
  { title: 'ID', align: 'start', sortable: false, key: 'id' },
  { title: 'Логин', key: 'username', align: 'end' },
  { title: 'ФИО', key: 'display_name', align: 'end' },
  { title: 'Email', key: 'email', align: 'end' },
  { title: 'Роль', key: 'role', align: 'center', sortable: false },
])

const serverItems = ref([])
const loading = ref(true)
const totalItems = ref(0)

const showCreateUserDialog = ref(false)
const newUser = ref({
  username: '',
  password: '',
  display_name: '',
  email: '',
  role: 'user',
})
const creatingUser = ref(false)
const createUserError = ref('')

let lastTableOptions = { page: 1, itemsPerPage: itemsPerPage.value }

const loadItems = async ({ page, itemsPerPage }) => {
  lastTableOptions = { page, itemsPerPage }
  loading.value = true
  try {
    const offset = (page - 1) * itemsPerPage
    const response = await http.get('/api/users/', {
      params: { offset, limit: itemsPerPage },
    })
    serverItems.value = response.data.items
    totalItems.value = response.data.total
  } catch (error) {
    console.error('Ошибка при загрузке пользователей:', error)
  } finally {
    loading.value = false
  }
}

const handleCreateUser = async () => {
  if (!newUser.value.username || !newUser.value.password) {
    createUserError.value = 'Логин и пароль обязательны'
    return
  }
  creatingUser.value = true
  createUserError.value = ''
  try {
    await http.post('/api/users/create', newUser.value)
    showCreateUserDialog.value = false
    newUser.value = {
      username: '',
      password: '',
      display_name: '',
      email: '',
      role: 'user',
    }
    await loadItems(lastTableOptions)
  } catch (error) {
    createUserError.value = (error.response && error.response.data && error.response.data.detail)
      || 'Не удалось создать пользователя.'
    console.error('Ошибка при создании пользователя:', error)
  } finally {
    creatingUser.value = false
  }
}
</script>
