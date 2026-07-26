<template>
  <div class="tw:min-h-screen tw:bg-gray-100">
    <AppToolbar />
    <main class="tw:md:pl-[232px]">
      <div class="tw:border-b tw:border-gray-200 tw:bg-white tw:px-8 tw:py-4">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">Подписчики</h1>
      </div>
      <div class="tw:px-8 tw:py-6">
        <div class="tw:max-w-3xl tw:space-y-4">

          <div class="tw:flex tw:items-center tw:gap-2 tw:flex-wrap">
            <form @submit.prevent="load" class="tw:flex tw:gap-2 tw:flex-1 tw:min-w-[16rem]">
              <input v-model="q" type="search" placeholder="Поиск по адресу…"
                     class="tw:flex-1 tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300">
              <button type="submit"
                      class="tw:px-4 tw:py-2 tw:text-sm tw:rounded-lg tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors">
                Найти
              </button>
            </form>
            <button @click="exportCsv" :disabled="!subscribers.length"
                    class="tw:px-3 tw:py-2 tw:text-sm tw:rounded-lg tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors tw:disabled:opacity-40">
              Выгрузить CSV
            </button>
            <button @click="copyAll" :disabled="!subscribers.length"
                    class="tw:px-3 tw:py-2 tw:text-sm tw:rounded-lg tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors tw:disabled:opacity-40">
              Скопировать адреса
            </button>
          </div>

          <p class="tw:text-sm tw:text-gray-500">
            {{ q ? `Найдено: ${total}` : `Всего подписок: ${total}` }}
          </p>
          <div v-if="error" class="tw:text-sm tw:text-red-600">{{ error }}</div>

          <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
            <table class="tw:w-full tw:text-sm">
              <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
                <tr>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Email</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Подписан</th>
                  <th class="tw:px-4 tw:py-3"></th>
                </tr>
              </thead>
              <tbody class="tw:divide-y tw:divide-gray-100">
                <tr v-for="s in subscribers" :key="s.id" class="tw:hover:bg-gray-50 tw:transition-colors">
                  <td class="tw:px-4 tw:py-3 tw:text-gray-800">{{ s.email }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500">{{ formatDate(s.created_at) }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-right">
                    <button @click="del(s)"
                            class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-red-200 tw:text-red-500 tw:hover:bg-red-50 tw:transition-colors">
                      Удалить
                    </button>
                  </td>
                </tr>
                <tr v-if="!subscribers.length && !loading">
                  <td colspan="3" class="tw:px-4 tw:py-10 tw:text-center tw:text-gray-400">
                    {{ q ? 'Ничего не найдено' : 'Подписчиков пока нет' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'

const router = useRouter()
const { hasRole } = useAuth()

const subscribers = ref([])
const total = ref(0)
const loading = ref(true)
const q = ref('')
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await http.get('/api/ceramic/subscribe', {
      params: { limit: 500, q: q.value || undefined },
    })
    subscribers.value = data.items || []
    total.value = data.total ?? subscribers.value.length
  } catch (err) {
    error.value = (err.response && err.response.data && err.response.data.detail) || 'Не удалось загрузить подписчиков.'
  } finally {
    loading.value = false
  }
}

async function del(s) {
  if (!confirm(`Удалить подписку ${s.email}?`)) return
  try {
    await http.delete(`/api/ceramic/subscribe/${s.id}`)
    subscribers.value = subscribers.value.filter((i) => i.id !== s.id)
    total.value -= 1
  } catch (err) {
    error.value = (err.response && err.response.data && err.response.data.detail) || 'Не удалось удалить подписку.'
  }
}

// Выгрузка идёт через blob: обычная ссылка не отправит cookie-заголовки axios-интерцептора
async function exportCsv() {
  const { data } = await http.get('/api/ceramic/subscribe/export', {
    params: { q: q.value || undefined },
    responseType: 'blob',
  })
  const url = URL.createObjectURL(data)
  const link = document.createElement('a')
  link.href = url
  link.download = 'subscribers.csv'
  link.click()
  URL.revokeObjectURL(url)
}

function copyAll() {
  navigator.clipboard.writeText(subscribers.value.map((s) => s.email).join(', '))
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
}

onMounted(() => {
  if (!hasRole('admin')) {
    router.push('/edit/access-denied')
    return
  }
  load()
})
</script>
