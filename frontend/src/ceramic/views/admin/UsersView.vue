<script setup>
import { ref, inject, onMounted } from 'vue'
import http from '../../api/http'
import { useAuth } from '../../composables/useAuth'

const heading = inject('adminHeading')
heading.value = 'Пользователи'
const { user: currentUser } = useAuth()

const users = ref([])
const openPasswordFor = ref(null)
const newPassword = ref('')

const newUsername = ref('')
const newUserPassword = ref('')
const newUserRole = ref('contributor')
const creating = ref(false)

async function load() {
  const { data } = await http.get('/api/ceramic/users', { params: { offset: 0, limit: 500 } })
  users.value = data.items
}
onMounted(load)

async function createUser() {
  creating.value = true
  try {
    await http.post('/api/ceramic/users', { username: newUsername.value, password: newUserPassword.value, role: newUserRole.value })
    newUsername.value = ''
    newUserPassword.value = ''
    newUserRole.value = 'contributor'
    await load()
  } finally {
    creating.value = false
  }
}

async function deleteUser(u) {
  if (!confirm(`Удалить пользователя «${u.username}»?`)) return
  await http.delete(`/api/ceramic/users/${u.id}`)
  await load()
}

function togglePasswordForm(u) {
  openPasswordFor.value = openPasswordFor.value === u.id ? null : u.id
  newPassword.value = ''
}

async function savePassword(u) {
  await http.put(`/api/ceramic/users/${u.id}/password`, { password: newPassword.value })
  openPasswordFor.value = null
  newPassword.value = ''
}
</script>

<template>
  <div class="tw:max-w-2xl tw:space-y-6">

    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
      <table class="tw:w-full tw:text-sm">
        <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
          <tr>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Имя пользователя</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Роль</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:sm:table-cell">Создан</th>
            <th class="tw:px-4 tw:py-3"></th>
          </tr>
        </thead>
        <tbody class="tw:divide-y tw:divide-gray-100">
          <tr v-for="u in users" :key="u.id" class="tw:hover:bg-gray-50 tw:transition-colors">
            <td class="tw:px-4 tw:py-3 tw:font-medium tw:text-gray-800">
              {{ u.username }}
              <span v-if="currentUser && u.username === currentUser.username" class="tw:ml-1.5 tw:text-xs tw:text-gray-400">(вы)</span>
            </td>
            <td class="tw:px-4 tw:py-3">
              <span v-if="u.role === 'admin'" class="tw:inline-block tw:px-2 tw:py-0.5 tw:rounded-full tw:text-xs tw:font-medium tw:bg-red-100 tw:text-red-700">Администратор</span>
              <span v-else class="tw:inline-block tw:px-2 tw:py-0.5 tw:rounded-full tw:text-xs tw:font-medium tw:bg-gray-100 tw:text-gray-600">Участник</span>
            </td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-400 tw:hidden tw:sm:table-cell tw:text-xs">{{ u.created_at }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-right">
              <div v-if="!currentUser || u.username !== currentUser.username" class="tw:flex tw:items-center tw:justify-end tw:gap-2 tw:relative">
                <button @click="togglePasswordForm(u)"
                        class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors">
                  Пароль
                </button>
                <div v-if="openPasswordFor === u.id"
                     class="tw:absolute tw:right-0 tw:top-8 tw:z-10 tw:bg-white tw:border tw:border-gray-200 tw:rounded-xl tw:shadow-lg tw:p-3 tw:w-52">
                  <form @submit.prevent="savePassword(u)" class="tw:flex tw:flex-col tw:gap-2">
                    <input v-model="newPassword" type="password" required placeholder="Новый пароль"
                           class="tw:rounded tw:border tw:border-gray-300 tw:px-2 tw:py-1 tw:text-xs tw:focus:outline-none tw:focus:ring-1 tw:focus:ring-red-300">
                    <button type="submit" class="tw:px-3 tw:py-1 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-xs tw:rounded tw:transition-colors">
                      Сохранить
                    </button>
                  </form>
                </div>
                <button @click="deleteUser(u)"
                        class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-red-200 tw:text-red-500 tw:hover:bg-red-50 tw:transition-colors">
                  Удалить
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!users.length">
            <td colspan="4" class="tw:px-4 tw:py-10 tw:text-center tw:text-gray-400">Нет пользователей</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
      <h2 class="tw:text-sm tw:font-semibold tw:text-gray-700 tw:mb-4">Добавить пользователя</h2>
      <form @submit.prevent="createUser" class="tw:space-y-4">
        <div class="tw:grid tw:grid-cols-2 tw:gap-4">
          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Имя пользователя</label>
            <input v-model="newUsername" type="text" required
                   class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
          </div>
          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Пароль</label>
            <input v-model="newUserPassword" type="password" required
                   class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
          </div>
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Роль</label>
          <select v-model="newUserRole"
                  class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
            <option value="contributor">Участник — только добавление документов</option>
            <option value="admin">Администратор — полный доступ</option>
          </select>
        </div>
        <button type="submit" :disabled="creating"
                class="tw:px-5 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
          Создать
        </button>
      </form>
    </div>

  </div>
</template>
