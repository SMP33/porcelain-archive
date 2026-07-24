<script setup>
import { ref, provide, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import http from '../api/http'

const route = useRoute()
const router = useRouter()
const { user, hasRole, logout } = useAuth()

const unreadFeedback = ref(0)
// Заголовок раздела задаётся дочерним view через inject('adminHeading')
const heading = ref('')
provide('adminHeading', heading)
provide('reloadUnreadFeedback', loadUnreadFeedback)

async function loadUnreadFeedback() {
  if (!hasRole('admin')) return
  try {
    const { data } = await http.get('/api/ceramic/feedback/unread_count')
    unreadFeedback.value = data.count
  } catch (error) {
    unreadFeedback.value = 0
  }
}

onMounted(loadUnreadFeedback)

function isSection(name) {
  return route.name === name || (route.name || '').startsWith(name)
}

async function onLogout() {
  await logout()
  router.push({ name: 'ceramic-admin-login' })
}
</script>

<template>
  <div class="ceramic-reset tw:bg-gray-100 tw:min-h-screen tw:flex">

    <!-- Sidebar -->
    <aside class="tw:w-52 tw:shrink-0 tw:bg-ink-900 tw:text-gray-300 tw:flex tw:flex-col tw:min-h-screen">
      <router-link to="/admin/feedback"
                   class="tw:px-5 tw:py-5 tw:border-b tw:border-white/10 tw:hover:opacity-80 tw:transition-opacity">
        <div class="tw:text-white tw:font-semibold tw:text-sm tw:leading-tight">Архив</div>
        <div class="tw:text-gray-500 tw:text-xs tw:mt-0.5">Управление</div>
      </router-link>
      <nav class="tw:flex tw:flex-col tw:py-3 tw:text-sm tw:flex-1">
        <template v-if="hasRole('admin')">
          <router-link to="/admin/feedback"
                       class="tw:px-5 tw:py-2.5 tw:hover:bg-white/10 tw:transition-colors tw:flex tw:items-center tw:gap-2"
                       :class="{ 'tw:bg-white/10 tw:text-white': isSection('ceramic-admin-feedback') }">
            <span>✉️ Обратная связь</span>
            <span v-if="unreadFeedback" class="tw:ml-auto tw:bg-red-600 tw:text-white tw:text-xs tw:font-semibold tw:rounded-full tw:px-1.5 tw:py-0.5 tw:min-w-[1.25rem] tw:text-center tw:leading-none">
              {{ unreadFeedback }}
            </span>
          </router-link>
          <router-link to="/admin/objects"
                       class="tw:px-5 tw:py-2.5 tw:hover:bg-white/10 tw:transition-colors"
                       :class="{ 'tw:bg-white/10 tw:text-white': isSection('ceramic-admin-objects') }">
            🏭 Объекты
          </router-link>
          <router-link to="/admin/users"
                       class="tw:px-5 tw:py-2.5 tw:hover:bg-white/10 tw:transition-colors"
                       :class="{ 'tw:bg-white/10 tw:text-white': isSection('ceramic-admin-users') }">
            👥 Пользователи
          </router-link>
        </template>
        <div class="tw:mt-auto tw:border-t tw:border-white/10 tw:pt-3">
          <div v-if="user" class="tw:px-5 tw:py-2 tw:text-xs tw:text-gray-500">{{ user.display_name || user.username }}</div>
          <a href="/" target="_blank" class="tw:px-5 tw:py-2.5 tw:hover:bg-white/10 tw:transition-colors tw:flex tw:items-center tw:gap-2">
            🌐 <span>Открыть сайт</span>
          </a>
          <button type="button" @click="onLogout"
                  class="tw:w-full tw:text-left tw:px-5 tw:py-2.5 tw:hover:bg-white/10 tw:transition-colors tw:text-gray-400">
            → Выйти
          </button>
        </div>
      </nav>
    </aside>

    <!-- Content -->
    <div class="tw:flex-1 tw:flex tw:flex-col tw:min-h-screen">
      <header class="tw:bg-white tw:border-b tw:border-gray-200 tw:px-8 tw:py-4">
        <h1 class="tw:text-lg tw:font-semibold tw:text-gray-800">{{ heading }}</h1>
      </header>
      <main class="tw:flex-1 tw:px-8 tw:py-6">
        <router-view />
      </main>
    </div>

  </div>
</template>
