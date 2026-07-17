<script setup>
import { ref, inject, onMounted } from 'vue'
import http from '../../api/http'

const heading = inject('adminHeading')
heading.value = 'Объекты'

const factories = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const { data } = await http.get('/api/ceramic/factories', { params: { offset: 0, limit: 500 } })
    factories.value = data.items
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function onDelete(f) {
  if (!confirm(`Удалить объект «${f.name}» и все его документы?`)) return
  await http.delete(`/api/ceramic/factories/${f.id}`)
  await load()
}
</script>

<template>
  <div>
    <div class="tw:flex tw:items-center tw:justify-between tw:mb-5">
      <p class="tw:text-sm tw:text-gray-500">{{ factories.length }} объект(а/ов)</p>
      <router-link to="/ceramic/admin/factories/new"
         class="tw:px-4 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:rounded-lg tw:transition-colors">
        + Добавить объект
      </router-link>
    </div>

    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
      <table class="tw:w-full tw:text-sm">
        <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
          <tr>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Название</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:sm:table-cell">Местонахождение</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:md:table-cell">Годы</th>
            <th class="tw:px-4 tw:py-3 tw:text-right tw:font-medium tw:text-gray-600">Документы</th>
            <th class="tw:px-4 tw:py-3"></th>
          </tr>
        </thead>
        <tbody class="tw:divide-y tw:divide-gray-100">
          <tr v-for="f in factories" :key="f.id" class="tw:hover:bg-gray-50 tw:transition-colors">
            <td class="tw:px-4 tw:py-3 tw:font-medium tw:text-gray-800">{{ f.name }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:sm:table-cell">{{ f.location || '—' }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:md:table-cell">{{ f.founded || '?' }} — {{ f.closed || 'н.в.' }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-right tw:text-gray-500">{{ f.doc_count }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-right">
              <div class="tw:flex tw:items-center tw:justify-end tw:gap-2">
                <router-link :to="`/ceramic/admin/factories/${f.id}/edit`"
                   class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors">
                  Изменить
                </router-link>
                <button @click="onDelete(f)"
                        class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-red-200 tw:text-red-500 tw:hover:bg-red-50 tw:transition-colors">
                  Удалить
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!factories.length && !loading">
            <td colspan="5" class="tw:px-4 tw:py-10 tw:text-center tw:text-gray-400">Объекты не добавлены</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
