<script setup>
import { ref, inject, onMounted } from 'vue'
import http from '../../api/http'

const heading = inject('adminHeading')
heading.value = 'Подписчики на новости'

const subscribers = ref([])

async function load() {
  const { data } = await http.get('/api/ceramic/subscribers', { params: { offset: 0, limit: 500 } })
  subscribers.value = data.items
}
onMounted(load)

async function onDelete(s) {
  if (!confirm(`Удалить ${s.email}?`)) return
  await http.delete(`/api/ceramic/subscribers/${s.id}`)
  await load()
}
</script>

<template>
  <div>
    <div class="tw:mb-4 tw:text-sm tw:text-gray-500">{{ subscribers.length }} подписчик(ов)</div>

    <div v-if="subscribers.length" class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
      <table class="tw:w-full tw:text-sm">
        <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
          <tr>
            <th class="tw:px-5 tw:py-3 tw:text-left tw:font-medium tw:text-gray-500">Email</th>
            <th class="tw:px-5 tw:py-3 tw:text-left tw:font-medium tw:text-gray-500">Дата подписки</th>
            <th class="tw:px-5 tw:py-3"></th>
          </tr>
        </thead>
        <tbody class="tw:divide-y tw:divide-gray-100">
          <tr v-for="s in subscribers" :key="s.id" class="tw:hover:bg-gray-50">
            <td class="tw:px-5 tw:py-3 tw:text-ink-800">{{ s.email }}</td>
            <td class="tw:px-5 tw:py-3 tw:text-gray-400">{{ s.created_at?.slice(0, 16) }}</td>
            <td class="tw:px-5 tw:py-3 tw:text-right">
              <button @click="onDelete(s)" class="tw:text-xs tw:text-red-500 tw:hover:text-red-700 tw:transition-colors">Удалить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="tw:text-center tw:py-20 tw:text-gray-300 tw:text-sm">Подписчиков пока нет</div>
  </div>
</template>
