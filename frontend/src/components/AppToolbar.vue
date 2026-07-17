<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { useAuth } from '../composables/useAuth'
import AppModal from './AppModal.vue'

const {
  user, hasRole, handleLogout,
  showResetPasswordDialog, oldPassword, newPassword, resetPasswordLoading, resetPasswordError, handleResetPassword,
  showSetDisplayNameDialog, displayNameInput, setDisplayNameLoading, setDisplayNameError, handleSetDisplayName,
} = useAuth()

const navItems = computed(() => {
  const items = [
    { to: '/', title: 'Документы', icon: 'mdi mdi-file-document-multiple-outline' },
    { to: '/branches', title: 'Наборы изменений', icon: 'mdi mdi-source-branch' },
    { to: '/tasks', title: 'Задачи', icon: 'mdi mdi-format-list-checks' },
    { to: '/users', title: 'Пользователи', icon: 'mdi mdi-account-group-outline' },
  ]
  if (hasRole('admin')) {
    items.push({ to: '/server-log', title: 'Лог сервера', icon: 'mdi mdi-text-box-search-outline' })
  }
  return items
})

const accountMenuOpen = ref(false)
const mobileMenuOpen = ref(false)
const accountMenuRoot = ref(null)
const mobileMenuRoot = ref(null)

function onDocClick(e) {
  if (accountMenuOpen.value && accountMenuRoot.value && !accountMenuRoot.value.contains(e.target)) {
    accountMenuOpen.value = false
  }
  if (mobileMenuOpen.value && mobileMenuRoot.value && !mobileMenuRoot.value.contains(e.target)) {
    mobileMenuOpen.value = false
  }
}
document.addEventListener('click', onDocClick, true)
onBeforeUnmount(() => document.removeEventListener('click', onDocClick, true))

function openResetPassword() {
  accountMenuOpen.value = false
  mobileMenuOpen.value = false
  showResetPasswordDialog.value = true
}

function openSetDisplayName() {
  accountMenuOpen.value = false
  mobileMenuOpen.value = false
  showSetDisplayNameDialog.value = true
}

function onLogoutClick() {
  accountMenuOpen.value = false
  mobileMenuOpen.value = false
  handleLogout()
}
</script>

<template>
  <!-- Десктоп: постоянный тёмный сайдбар слева -->
  <aside class="tw:hidden tw:md:flex tw:flex-col tw:fixed tw:inset-y-0 tw:left-0 tw:w-[232px] tw:bg-ink-900 tw:text-gray-300 tw:z-20">
    <router-link to="/" class="tw:flex tw:items-center tw:gap-3 tw:px-5 tw:py-5 tw:text-white tw:no-underline tw:border-b tw:border-white/10">
      <span class="tw:flex tw:items-center tw:justify-center tw:w-8 tw:h-8 tw:shrink-0 tw:rounded tw:bg-clay-500" style="transform: skewX(-10deg);">
        <i class="mdi mdi-book-open-page-variant tw:text-white tw:text-lg" style="transform: skewX(10deg); display: inline-block;" />
      </span>
      <span class="tw:font-serif tw:font-bold tw:text-base tw:leading-tight">Архив</span>
    </router-link>

    <nav class="tw:flex-1 tw:overflow-y-auto tw:px-2 tw:py-3 tw:space-y-1">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="tw:flex tw:items-center tw:gap-3 tw:px-3 tw:py-2 tw:rounded-lg tw:text-sm tw:transition-colors tw:hover:bg-white/10"
        active-class="tw:bg-white/10 tw:text-white"
      >
        <i :class="item.icon" class="tw:text-lg" />
        {{ item.title }}
      </router-link>
    </nav>

    <div class="tw:border-t tw:border-white/10 tw:pt-3 tw:pb-6 tw:px-2">
      <div v-if="user" class="tw:px-3 tw:pb-2 tw:text-xs tw:text-white/45 tw:truncate">{{ user.display_name || user.username }}</div>

      <div v-if="user" ref="accountMenuRoot" class="tw:relative">
        <button
          type="button"
          class="tw:w-full tw:flex tw:items-center tw:gap-3 tw:px-3 tw:py-2 tw:rounded-lg tw:text-sm tw:hover:bg-white/10 tw:transition-colors"
          @click="accountMenuOpen = !accountMenuOpen"
        >
          <i class="mdi mdi-account-cog tw:text-lg" /> Аккаунт
        </button>
        <div
          v-if="accountMenuOpen"
          class="tw:absolute tw:bottom-full tw:left-2 tw:mb-1 tw:w-48 tw:bg-white tw:rounded-lg tw:shadow-lg tw:border tw:border-gray-200 tw:py-1 tw:text-ink-900"
        >
          <router-link to="/tasks" class="tw:block tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50" @click="accountMenuOpen = false">Список задач</router-link>
          <button type="button" class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50" @click="openResetPassword">Сменить пароль</button>
          <button type="button" class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50" @click="openSetDisplayName">Изменить ФИО</button>
          <div class="tw:my-1 tw:border-t tw:border-gray-100" />
          <button type="button" class="tw:flex tw:items-center tw:gap-2 tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50" @click="onLogoutClick">
            <i class="mdi mdi-logout" /> Выйти
          </button>
        </div>
      </div>
      <router-link v-else to="/login" class="tw:flex tw:items-center tw:gap-3 tw:px-3 tw:py-2 tw:rounded-lg tw:text-sm tw:hover:bg-white/10 tw:transition-colors">
        <i class="mdi mdi-login tw:text-lg" /> Войти
      </router-link>
    </div>
  </aside>

  <!-- Мобильный вариант: тёмный топбар с гамбургер-меню -->
  <header class="tw:md:hidden tw:sticky tw:top-0 tw:z-20 tw:flex tw:items-center tw:bg-ink-900 tw:text-white tw:h-14 tw:px-4">
    <router-link to="/" class="tw:flex tw:items-center tw:gap-2 tw:text-white tw:no-underline">
      <span class="tw:flex tw:items-center tw:justify-center tw:w-7 tw:h-7 tw:shrink-0 tw:rounded tw:bg-clay-500" style="transform: skewX(-10deg);">
        <i class="mdi mdi-book-open-page-variant tw:text-white tw:text-base" style="transform: skewX(10deg); display: inline-block;" />
      </span>
      <span class="tw:font-serif tw:font-bold tw:text-sm">Архив</span>
    </router-link>
    <div class="tw:flex-1" />
    <div ref="mobileMenuRoot" class="tw:relative">
      <button type="button" class="tw:p-2 tw:text-white" @click="mobileMenuOpen = !mobileMenuOpen">
        <i class="mdi mdi-menu tw:text-xl" />
      </button>
      <div
        v-if="mobileMenuOpen"
        class="tw:absolute tw:right-0 tw:mt-2 tw:w-56 tw:bg-white tw:rounded-lg tw:shadow-lg tw:border tw:border-gray-200 tw:py-1 tw:text-ink-900"
      >
        <div v-if="user" class="tw:px-3 tw:py-2 tw:text-xs tw:text-gray-400 tw:truncate">{{ user.display_name || user.username }}</div>

        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="tw:flex tw:items-center tw:gap-2 tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50"
          @click="mobileMenuOpen = false"
        >
          <i :class="item.icon" /> {{ item.title }}
        </router-link>

        <div v-if="user" class="tw:my-1 tw:border-t tw:border-gray-100" />

        <button v-if="user" type="button" class="tw:flex tw:items-center tw:gap-2 tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50" @click="openResetPassword">
          <i class="mdi mdi-lock-reset" /> Сменить пароль
        </button>
        <button v-if="user" type="button" class="tw:flex tw:items-center tw:gap-2 tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50" @click="openSetDisplayName">
          <i class="mdi mdi-account-edit" /> Изменить ФИО
        </button>
        <button v-if="user" type="button" class="tw:flex tw:items-center tw:gap-2 tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50" @click="onLogoutClick">
          <i class="mdi mdi-logout" /> Выйти
        </button>
        <router-link v-else to="/login" class="tw:flex tw:items-center tw:gap-2 tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50" @click="mobileMenuOpen = false">
          <i class="mdi mdi-login" /> Войти
        </router-link>
      </div>
    </div>
  </header>

  <AppModal v-model="showResetPasswordDialog" max-width="tw:max-w-sm">
    <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">Смена пароля</h2>
    <div class="tw:space-y-4">
      <div>
        <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Текущий пароль</label>
        <input v-model="oldPassword" type="password" autofocus
               class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300">
      </div>
      <div>
        <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Новый пароль</label>
        <input v-model="newPassword" type="password" @keyup.enter="handleResetPassword"
               class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300">
      </div>
      <div v-if="resetPasswordError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2">
        {{ resetPasswordError }}
      </div>
    </div>
    <div class="tw:flex tw:items-center tw:justify-end tw:gap-2 tw:mt-6">
      <button type="button" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors" @click="showResetPasswordDialog = false">Отмена</button>
      <button type="button" :disabled="resetPasswordLoading"
              class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
              @click="handleResetPassword">
        {{ resetPasswordLoading ? 'Сохранение…' : 'Сохранить' }}
      </button>
    </div>
  </AppModal>

  <AppModal v-model="showSetDisplayNameDialog" max-width="tw:max-w-sm">
    <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">Изменение ФИО</h2>
    <div class="tw:space-y-4">
      <div>
        <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">ФИО</label>
        <input v-model="displayNameInput" type="text" autofocus @keyup.enter="handleSetDisplayName"
               class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300">
      </div>
      <div v-if="setDisplayNameError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2">
        {{ setDisplayNameError }}
      </div>
    </div>
    <div class="tw:flex tw:items-center tw:justify-end tw:gap-2 tw:mt-6">
      <button type="button" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors" @click="showSetDisplayNameDialog = false">Отмена</button>
      <button type="button" :disabled="setDisplayNameLoading"
              class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
              @click="handleSetDisplayName">
        {{ setDisplayNameLoading ? 'Сохранение…' : 'Сохранить' }}
      </button>
    </div>
  </AppModal>
</template>
