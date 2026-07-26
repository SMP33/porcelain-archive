<template>
  <div class="tw:min-h-screen tw:bg-gray-100">
    <AppToolbar />
    <main class="tw:md:pl-[232px]">
      <div class="tw:border-b tw:border-gray-200 tw:bg-white tw:px-8 tw:py-4 tw:flex tw:items-center tw:justify-between">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">Документы</h1>
        <button
          v-if="user"
          type="button"
          class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors"
          @click="showCreateDialog = true"
        >
          Добавить документ
        </button>
      </div>
      <div class="tw:px-8 tw:py-6">
        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
          <div class="tw:overflow-x-auto">
            <table class="tw:w-full tw:text-sm">
              <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
                <tr>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">ID</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Название документа</th>
                </tr>
              </thead>
              <tbody class="tw:divide-y tw:divide-gray-100">
                <tr
                  v-for="item in items"
                  :key="item.id"
                  class="tw:cursor-pointer tw:hover:bg-clay-50/60 tw:transition-colors"
                  @click="openDocument(item)"
                >
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500">{{ item.id }}</td>
                  <td class="tw:px-4 tw:py-3 tw:font-medium tw:text-gray-800">{{ item.name }}</td>
                </tr>
                <tr v-if="!loading && !items.length">
                  <td colspan="2" class="tw:px-4 tw:py-8 tw:text-center tw:text-gray-400">Нет данных</td>
                </tr>
                <tr v-if="loading">
                  <td colspan="2" class="tw:px-4 tw:py-8 tw:text-center tw:text-gray-400">Загрузка…</td>
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

    <AppModal v-model="showCreateDialog" max-width="tw:max-w-md">
      <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">Новый документ</h2>
      <div class="tw:space-y-4">
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Название документа</label>
          <input
            v-model="newDocumentName"
            type="text"
            autofocus
            class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"
            @keyup.enter="handleCreateDocument"
          >
        </div>
        <div v-if="createError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2">
          {{ createError }}
        </div>
      </div>
      <div class="tw:flex tw:items-center tw:justify-end tw:gap-2 tw:mt-6">
        <button type="button" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors" @click="showCreateDialog = false">Отмена</button>
        <button
          type="button"
          :disabled="creating"
          class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
          @click="handleCreateDocument"
        >
          {{ creating ? 'Создание…' : 'Создать' }}
        </button>
      </div>
    </AppModal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'
import AppPager from '../components/AppPager.vue'
import AppModal from '../components/AppModal.vue'
import { usePagedTable } from '../composables/usePagedTable'

const router = useRouter()
const { user } = useAuth()

const { page, itemsPerPage, items, total, loading, pageCount, reload, goToPage, setItemsPerPage } = usePagedTable(
  async ({ offset, limit }) => {
    const response = await http.get('/api/documents/', { params: { offset, limit } })
    return { items: response.data.items, total: response.data.total }
  },
)

const showCreateDialog = ref(false)
const newDocumentName = ref('')
const creating = ref(false)
const createError = ref('')

function openDocument(item) {
  router.push(`/edit/document/${item.id}`)
}

const handleCreateDocument = async () => {
  if (!newDocumentName.value) {
    return
  }
  creating.value = true
  createError.value = ''
  try {
    const response = await http.post('/api/documents/create', { name: newDocumentName.value })
    router.push(`/edit/document/${response.data.id}`)
  } catch (error) {
    createError.value = 'Не удалось создать документ.'
    console.error('Ошибка при создании документа:', error)
  } finally {
    creating.value = false
  }
}

onMounted(reload)
</script>
