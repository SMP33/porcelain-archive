<script setup>
import { ref, inject, onMounted } from 'vue'
import http from '../../api/http'

const heading = inject('adminHeading')
heading.value = 'Обратная связь'
const reloadUnread = inject('reloadUnreadFeedback')

const messages = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const { data } = await http.get('/api/ceramic/feedback', { params: { offset: 0, limit: 200 } })
    messages.value = data.items
  } finally {
    loading.value = false
  }
}
onMounted(load)

function initial(name) {
  return (name || 'А')[0].toUpperCase()
}

async function setImportant(m) {
  await http.patch(`/api/ceramic/feedback/${m.id}`, { is_important: !m.is_important })
  await load()
}
async function setRead(m, isRead) {
  await http.patch(`/api/ceramic/feedback/${m.id}`, { is_read: isRead })
  await load()
  if (reloadUnread) reloadUnread()
}
</script>

<template>
  <div>
    <p class="tw:text-sm tw:text-gray-500 tw:mb-5">{{ messages.length }} сообщений(я)</p>

    <div v-if="messages.length" class="tw:space-y-4">
      <div v-for="m in messages" :key="m.id"
           class="tw:bg-white tw:rounded-xl tw:border tw:p-5"
           :class="!m.is_read ? 'tw:border-red-200 tw:ring-1 tw:ring-red-100' : (m.is_important ? 'tw:border-yellow-200' : 'tw:border-gray-200')">

        <div class="tw:flex tw:items-start tw:justify-between tw:gap-4 tw:mb-3">
          <div class="tw:flex tw:items-center tw:gap-3">
            <div class="tw:w-8 tw:h-8 tw:rounded-full tw:flex tw:items-center tw:justify-center tw:font-semibold tw:text-sm tw:shrink-0"
                 :class="!m.is_read ? 'tw:bg-red-100 tw:text-red-700' : (m.is_important ? 'tw:bg-yellow-100 tw:text-yellow-700' : 'tw:bg-gray-100 tw:text-gray-500')">
              {{ initial(m.name) }}
            </div>
            <div>
              <div class="tw:flex tw:items-center tw:gap-2">
                <p class="tw:text-sm tw:font-medium tw:text-gray-800">{{ m.name || 'Аноним' }}</p>
                <span v-if="!m.is_read" class="tw:text-xs tw:bg-red-100 tw:text-red-700 tw:font-medium tw:px-1.5 tw:py-0.5 tw:rounded-full">Новое</span>
                <span v-if="m.is_important" class="tw:text-xs tw:bg-yellow-100 tw:text-yellow-700 tw:font-medium tw:px-1.5 tw:py-0.5 tw:rounded-full">Важное</span>
              </div>
              <a v-if="m.email" :href="`mailto:${m.email}`" class="tw:text-xs tw:text-red-600 tw:hover:underline">{{ m.email }}</a>
            </div>
          </div>

          <div class="tw:flex tw:items-center tw:gap-2 tw:shrink-0">
            <span class="tw:text-xs tw:text-gray-400 tw:mr-1">{{ m.created_at }}</span>

            <button @click="setImportant(m)" :title="m.is_important ? 'Снять метку важного' : 'Отметить важным'"
                    class="tw:text-sm tw:px-2.5 tw:py-1 tw:rounded tw:border tw:transition-colors"
                    :class="m.is_important ? 'tw:border-yellow-300 tw:bg-yellow-50 tw:text-yellow-600 tw:hover:bg-yellow-100' : 'tw:border-gray-200 tw:text-gray-400 tw:hover:bg-gray-50 tw:hover:text-yellow-500'">
              ★
            </button>

            <button v-if="m.is_read" @click="setRead(m, false)"
                    class="tw:text-xs tw:px-3 tw:py-1 tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:text-gray-400 tw:transition-colors">
              Непрочитано
            </button>
            <button v-if="!m.is_read" @click="setRead(m, true)"
                    class="tw:text-xs tw:px-3 tw:py-1 tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:text-gray-500 tw:transition-colors">
              ✓ Прочитано
            </button>
          </div>
        </div>

        <p class="tw:text-sm tw:text-gray-700 tw:leading-relaxed tw:whitespace-pre-wrap">{{ m.message }}</p>
      </div>
    </div>

    <div v-else-if="!loading" class="tw:text-center tw:py-16 tw:text-gray-400">
      <p>Сообщений пока нет</p>
    </div>
  </div>
</template>
