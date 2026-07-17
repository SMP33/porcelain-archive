<template>
  <div class="tw:min-h-screen tw:bg-gray-100">
    <AppToolbar />
    <main class="tw:md:pl-[232px]">
      <div class="tw:border-b tw:border-gray-200 tw:bg-white tw:px-8 tw:py-4">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">Наборы изменений</h1>
      </div>
      <div class="tw:px-8 tw:py-6">
        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
          <div class="tw:overflow-x-auto">
            <table class="tw:w-full tw:text-sm">
              <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
                <tr>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">ID</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Название</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:sm:table-cell">Автор</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:md:table-cell">Создан</th>
                  <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:lg:table-cell">Изменён</th>
                  <th class="tw:px-4 tw:py-3 tw:text-right tw:font-medium tw:text-gray-600">Статус</th>
                </tr>
              </thead>
              <tbody class="tw:divide-y tw:divide-gray-100">
                <tr
                  v-for="item in items"
                  :key="item.id"
                  class="tw:cursor-pointer tw:hover:bg-clay-50/60 tw:transition-colors"
                  @click="openBranch(item)"
                >
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500">{{ item.id }}</td>
                  <td class="tw:px-4 tw:py-3 tw:font-medium tw:text-gray-800">{{ item.document_name }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:sm:table-cell">{{ item.author_name }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:md:table-cell">{{ item.created_at }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:lg:table-cell">{{ item.last_change_at }}</td>
                  <td class="tw:px-4 tw:py-3 tw:text-right">
                    <span class="tw:inline-block tw:px-2 tw:py-0.5 tw:rounded-full tw:text-xs tw:font-medium" :class="statusClass(item.status)">
                      {{ statusLabels[item.status] || item.status }}
                    </span>
                  </td>
                </tr>
                <tr v-if="!loading && !items.length">
                  <td colspan="6" class="tw:px-4 tw:py-8 tw:text-center tw:text-gray-400">Нет данных</td>
                </tr>
                <tr v-if="loading">
                  <td colspan="6" class="tw:px-4 tw:py-8 tw:text-center tw:text-gray-400">Загрузка…</td>
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
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '../api/http'
import AppToolbar from '../components/AppToolbar.vue'
import AppPager from '../components/AppPager.vue'
import { usePagedTable } from '../composables/usePagedTable'

const router = useRouter()

const statusLabels = {
  in_work: 'В работе',
  in_review: 'Проверяется',
  in_accept: 'Завершение правок',
  accepted: 'Принято',
  rejected: 'Отклонено',
}
const statusClasses = {
  in_work: 'tw:bg-blue-100 tw:text-blue-700',
  in_review: 'tw:bg-purple-100 tw:text-purple-700',
  in_accept: 'tw:bg-teal-100 tw:text-teal-700',
  accepted: 'tw:bg-green-100 tw:text-green-700',
  rejected: 'tw:bg-red-100 tw:text-red-700',
}
function statusClass(status) {
  return statusClasses[status] || 'tw:bg-gray-100 tw:text-gray-600'
}

const { page, itemsPerPage, items, total, loading, pageCount, reload, goToPage, setItemsPerPage } = usePagedTable(
  async ({ offset, limit }) => {
    const response = await http.get('/api/documents/branches/', { params: { offset, limit } })
    return { items: response.data.items, total: response.data.total }
  },
)

function openBranch(item) {
  router.push(`/edit/${item.id}`)
}

onMounted(reload)
</script>
