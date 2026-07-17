<template>
  <div class="tw:min-h-screen tw:bg-gray-100">
    <AppToolbar />
    <main class="tw:md:pl-[232px]">
      <div class="tw:border-b tw:border-gray-200 tw:bg-white tw:px-8 tw:py-4">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">{{ document ? document.name : 'Документ' }}</h1>
      </div>
      <div class="tw:px-8 tw:py-6 tw:space-y-4">
        <div v-if="!loading && document && hasRole('moderator')" class="tw:flex tw:gap-1 tw:border-b tw:border-gray-200">
          <button
            type="button"
            class="tw:px-4 tw:py-2 tw:text-sm tw:font-medium tw:border-b-2 tw:transition-colors"
            :class="activeTab === 'document' ? 'tw:border-clay-500 tw:text-clay-600' : 'tw:border-transparent tw:text-gray-500 tw:hover:text-gray-700'"
            @click="activeTab = 'document'"
          >
            Документ
          </button>
          <button
            type="button"
            class="tw:px-4 tw:py-2 tw:text-sm tw:font-medium tw:border-b-2 tw:transition-colors"
            :class="activeTab === 'pages' ? 'tw:border-clay-500 tw:text-clay-600' : 'tw:border-transparent tw:text-gray-500 tw:hover:text-gray-700'"
            @click="activeTab = 'pages'"
          >
            Страницы документа
          </button>
        </div>

        <div v-if="!loading && document && (!hasRole('moderator') || activeTab === 'document')" class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
          <div class="tw:text-sm tw:text-gray-500 tw:mb-4">Автор: {{ document.author }} | Создан: {{ document.created_at }}</div>

          <div v-if="hasRole('moderator')" class="tw:flex tw:items-center tw:mb-4">
            <button
              type="button"
              role="switch"
              :aria-checked="document.is_visible"
              :disabled="visibilityLoading"
              class="tw:relative tw:inline-flex tw:items-center tw:h-6 tw:w-11 tw:rounded-full tw:transition-colors tw:disabled:opacity-50"
              :class="document.is_visible ? 'tw:bg-clay-500' : 'tw:bg-gray-300'"
              @click="handleToggleVisibility(!document.is_visible)"
            >
              <span
                class="tw:inline-block tw:w-4 tw:h-4 tw:bg-white tw:rounded-full tw:shadow tw:transform tw:transition-transform"
                :class="document.is_visible ? 'tw:translate-x-6' : 'tw:translate-x-1'"
              />
            </button>
            <span class="tw:ml-2 tw:text-sm tw:text-gray-600">
              {{ document.is_visible ? 'Виден всем пользователям' : 'Скрыт от обычных пользователей' }}
            </span>
          </div>

          <p class="tw:text-sm tw:text-gray-600">Это страница для просмотра документа с ID: <strong>{{ document.id }}</strong>.</p>
          <p class="tw:text-sm tw:text-gray-600 tw:mt-1">Здесь будет содержимое документа.</p>

          <div class="tw:flex tw:items-center tw:gap-3 tw:mt-5">
            <router-link to="/edit" class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors">Назад к списку</router-link>
            <button
              v-if="user"
              type="button"
              :disabled="creatingBranch"
              class="tw:px-5 tw:py-2 tw:bg-ink-900 tw:hover:bg-ink-800 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
              @click="handleEditDocument"
            >
              {{ creatingBranch ? 'Создание…' : 'Редактировать документ' }}
            </button>
          </div>
          <div v-if="editError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
            {{ editError }}
          </div>
        </div>

        <div v-if="!loading && document && hasRole('moderator') && activeTab === 'document'" class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
          <h2 class="tw:px-6 tw:pt-5 tw:text-sm tw:font-semibold tw:text-gray-700">Наборы изменений</h2>
          <div class="tw:overflow-x-auto tw:mt-3">
            <table class="tw:w-full tw:text-sm">
              <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
                <tr>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">ID</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Автор</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:sm:table-cell">Создан</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:md:table-cell">Изменён</th>
                  <th class="tw:px-4 tw:py-3 tw:text-right tw:font-medium tw:text-gray-600">Статус</th>
                </tr>
              </thead>
              <tbody class="tw:divide-y tw:divide-gray-100">
                <tr
                  v-for="item in branchItems"
                  :key="item.id"
                  class="tw:cursor-pointer tw:hover:bg-clay-50/60 tw:transition-colors"
                  @click="openBranch(item)"
                >
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500">{{ item.id }}</td>
                  <td class="tw:px-4 tw:py-3 tw:font-medium tw:text-gray-800">{{ item.author_name }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:sm:table-cell">{{ item.created_at }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:md:table-cell">{{ item.last_change_at }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-right">
                    <span class="tw:inline-block tw:px-2 tw:py-0.5 tw:rounded-full tw:text-xs tw:font-medium" :class="branchStatusClass(item.status)">
                      {{ branchStatusLabels[item.status] || item.status }}
                    </span>
                  </td>
                </tr>
                <tr v-if="!branchesLoading && !branchItems.length">
                  <td colspan="5" class="tw:px-4 tw:py-8 tw:text-center tw:text-gray-400">Нет данных</td>
                </tr>
                <tr v-if="branchesLoading">
                  <td colspan="5" class="tw:px-4 tw:py-8 tw:text-center tw:text-gray-400">Загрузка…</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="tw:px-4 tw:pb-4">
            <AppPager
              :page="branchesPage"
              :page-count="branchesPageCount"
              :items-per-page="branchesItemsPerPage"
              :items-per-page-options="[25, 50, 100]"
              :total="branchesTotal"
              @update:page="branchesGoToPage"
              @update:items-per-page="branchesSetItemsPerPage"
            />
          </div>
        </div>

        <div v-if="!loading && document && masterBranchId && (!hasRole('moderator') || activeTab === 'pages')" class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
          <h2 class="tw:text-sm tw:font-semibold tw:text-gray-700 tw:mb-4">Страницы</h2>
          <div v-if="galleryLoading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
          <div v-else-if="!galleryPageCount" class="tw:text-sm tw:text-gray-400">Страниц пока нет</div>
          <div v-else class="tw:grid tw:grid-cols-2 tw:sm:grid-cols-3 tw:md:grid-cols-4 tw:lg:grid-cols-6 tw:gap-3">
            <div
              v-for="pos in galleryPageCount"
              :key="pos"
              class="tw:cursor-pointer tw:bg-white tw:rounded-lg tw:border tw:border-gray-200 tw:overflow-hidden tw:hover:border-clay-300 tw:hover:shadow-md tw:transition-all"
              @click="galleryRef.show(pos)"
            >
              <img :src="galleryRef && galleryRef.previewImageUrl(pos)" class="tw:w-full tw:h-[120px] tw:object-cover">
              <div class="tw:text-xs tw:text-gray-500 tw:text-center tw:p-1">{{ pos }}</div>
            </div>
          </div>
        </div>

        <PageGalleryViewer
          v-if="masterBranchId"
          ref="galleryRef"
          :branch-id="masterBranchId"
          :page-count="galleryPageCount"
        />

        <div v-if="loading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
        <div v-if="error" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2">{{ error }}</div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'
import AppPager from '../components/AppPager.vue'
import PageGalleryViewer from '../components/PageGalleryViewer.vue'
import { usePagedTable } from '../composables/usePagedTable'

const route = useRoute()
const router = useRouter()
const { user, hasRole } = useAuth()

const document = ref(null)
const loading = ref(true)
const error = ref(null)

const creatingBranch = ref(false)
const editError = ref('')

const visibilityLoading = ref(false)

const activeTab = ref('document')

const masterBranchId = ref(null)
const galleryPageCount = ref(0)
const galleryLoading = ref(true)
const galleryRef = ref(null)

const branchStatusLabels = {
  in_work: 'В работе',
  in_review: 'Проверяется',
  in_accept: 'Завершение правок',
  accepted: 'Принято',
  rejected: 'Отклонено',
}
const branchStatusClasses = {
  in_work: 'tw:bg-blue-100 tw:text-blue-700',
  in_review: 'tw:bg-purple-100 tw:text-purple-700',
  in_accept: 'tw:bg-teal-100 tw:text-teal-700',
  accepted: 'tw:bg-green-100 tw:text-green-700',
  rejected: 'tw:bg-red-100 tw:text-red-700',
}
function branchStatusClass(status) {
  return branchStatusClasses[status] || 'tw:bg-gray-100 tw:text-gray-600'
}

const {
  page: branchesPage,
  itemsPerPage: branchesItemsPerPage,
  items: branchItems,
  total: branchesTotal,
  loading: branchesLoading,
  pageCount: branchesPageCount,
  reload: reloadBranches,
  goToPage: branchesGoToPage,
  setItemsPerPage: branchesSetItemsPerPage,
} = usePagedTable(async ({ offset, limit }) => {
  const response = await http.get(`/api/documents/${document.value.id}/branches`, { params: { offset, limit } })
  return { items: response.data.items, total: response.data.total }
})

const loadDocument = async (id) => {
  try {
    const response = await http.get(`/api/documents/${id}`)
    document.value = response.data
  } catch (err) {
    const status = err.response ? err.response.status : null
    if (status === 401) {
      router.push({ name: 'login', query: { redirect: route.fullPath } })
      return
    }
    if (status === 403 || status === 404) {
      router.push('/edit/access-denied')
      return
    }
    error.value = 'Не удалось загрузить документ.'
    console.error('Ошибка при загрузке документа:', err)
  } finally {
    loading.value = false
  }
}

const loadGallery = async () => {
  galleryLoading.value = true
  try {
    const branchResponse = await http.get(`/api/documents/${document.value.id}/master_branch_id`)
    masterBranchId.value = branchResponse.data.branch_id

    const countResponse = await http.get(`/api/documents/branches/${masterBranchId.value}/pages/count`)
    galleryPageCount.value = countResponse.data.count
  } catch (err) {
    console.error('Ошибка при получении страниц документа:', err)
  } finally {
    galleryLoading.value = false
  }
}

const openBranch = (item) => {
  router.push(`/edit/${item.id}`)
}

const handleToggleVisibility = async (isVisible) => {
  visibilityLoading.value = true
  try {
    await http.post(`/api/documents/${document.value.id}/visibility`, { is_visible: isVisible })
    document.value.is_visible = isVisible
  } catch (err) {
    console.error('Ошибка при изменении видимости документа:', err)
  } finally {
    visibilityLoading.value = false
  }
}

const handleEditDocument = async () => {
  creatingBranch.value = true
  editError.value = ''
  try {
    const response = await http.post(`/api/documents/${document.value.id}/create_branch`, {})
    router.push(`/edit/${response.data.branch_id}`)
  } catch (err) {
    editError.value = 'Не удалось создать набор изменений для редактирования.'
    console.error('Ошибка при создании ветки:', err)
  } finally {
    creatingBranch.value = false
  }
}

onMounted(async () => {
  await loadDocument(route.params.documentId)
  if (document.value) {
    loadGallery()
    if (hasRole('moderator')) reloadBranches()
  }
})
</script>
