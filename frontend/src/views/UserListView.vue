<template>
  <div class="tw:min-h-screen tw:bg-gray-100">
    <AppToolbar />
    <main class="tw:md:pl-[232px]">
      <div class="tw:border-b tw:border-gray-200 tw:bg-white tw:px-8 tw:py-4 tw:flex tw:items-center tw:justify-between">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">Пользователи</h1>
        <button
          v-if="hasRole('admin')"
          type="button"
          class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors"
          @click="showCreateUserDialog = true"
        >
          Создать пользователя
        </button>
      </div>
      <div class="tw:px-8 tw:py-6">
        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
          <div class="tw:overflow-x-auto">
            <table class="tw:w-full tw:text-sm">
              <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
                <tr>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">ID</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Логин</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:sm:table-cell">ФИО</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:md:table-cell">Email</th>
                  <th class="tw:px-4 tw:py-3 tw:text-right tw:font-medium tw:text-gray-600">Роль</th>
                </tr>
              </thead>
              <tbody class="tw:divide-y tw:divide-gray-100">
                <tr v-for="item in items" :key="item.id" class="tw:transition-colors">
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500">{{ item.id }}</td>
                  <td class="tw:px-4 tw:py-3 tw:font-medium tw:text-gray-800">{{ item.username }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:sm:table-cell">{{ item.display_name }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:md:table-cell">{{ item.email }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-right tw:text-gray-500">{{ roleLabels[item.role] || item.role }}</td>
                </tr>
                <tr v-if="!loading && !items.length">
                  <td colspan="5" class="tw:px-4 tw:py-8 tw:text-center tw:text-gray-400">Нет данных</td>
                </tr>
                <tr v-if="loading">
                  <td colspan="5" class="tw:px-4 tw:py-8 tw:text-center tw:text-gray-400">Загрузка…</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="tw:px-4 tw:pb-4">
            <AppPager
              :page="page"
              :page-count="pageCount"
              :items-per-page="itemsPerPage"
              :items-per-page-options="[25, 50, 100, 500]"
              :total="total"
              @update:page="goToPage"
              @update:items-per-page="setItemsPerPage"
            />
          </div>
        </div>
      </div>
    </main>

    <AppModal v-model="showCreateUserDialog" max-width="tw:max-w-md">
      <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">Новый пользователь</h2>
      <div class="tw:space-y-4">
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Логин</label>
          <input v-model="newUser.username" type="text" autofocus
                 class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300">
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Пароль</label>
          <input v-model="newUser.password" type="password"
                 class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300">
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">ФИО</label>
          <input v-model="newUser.display_name" type="text"
                 class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300">
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Email</label>
          <input v-model="newUser.email" type="email"
                 class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300">
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Роль</label>
          <select
            v-model="newUser.role"
            class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"
          >
            <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">{{ opt.title }}</option>
          </select>
        </div>
        <div v-if="createUserError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2">
          {{ createUserError }}
        </div>
      </div>
      <div class="tw:flex tw:items-center tw:justify-end tw:gap-2 tw:mt-6">
        <button type="button" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors" @click="showCreateUserDialog = false">Отмена</button>
        <button
          type="button"
          :disabled="creatingUser"
          class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
          @click="handleCreateUser"
        >
          {{ creatingUser ? 'Создание…' : 'Создать' }}
        </button>
      </div>
    </AppModal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'
import AppPager from '../components/AppPager.vue'
import AppModal from '../components/AppModal.vue'
import { usePagedTable } from '../composables/usePagedTable'

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

const { page, itemsPerPage, items, total, loading, pageCount, reload, goToPage, setItemsPerPage } = usePagedTable(
  async ({ offset, limit }) => {
    const response = await http.get('/api/users/', { params: { offset, limit } })
    return { items: response.data.items, total: response.data.total }
  },
)

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
    await reload()
  } catch (error) {
    createUserError.value = (error.response && error.response.data && error.response.data.detail)
      || 'Не удалось создать пользователя.'
    console.error('Ошибка при создании пользователя:', error)
  } finally {
    creatingUser.value = false
  }
}

onMounted(reload)
</script>
