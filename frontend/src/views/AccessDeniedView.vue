<template>
  <div>
    <main>
      <div class="tw:mb-4">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">Страница недоступна</h1>
      </div>
      <div>
        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6 tw:max-w-xl">
          <div class="tw:text-sm tw:text-amber-700 tw:bg-amber-50 tw:border tw:border-amber-200 tw:rounded-lg tw:px-4 tw:py-3">
            У вас недостаточно прав для просмотра этой страницы, либо она не существует.
          </div>
          <div class="tw:flex tw:items-center tw:gap-3 tw:mt-4">
            <router-link
              to="/admin"
              class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors"
            >
              На главную
            </router-link>
            <router-link
              v-if="!user"
              to="/admin/login"
              class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors"
            >
              Войти
            </router-link>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { useAuth } from '../ceramic/composables/useAuth'

const { user } = useAuth()
</script>
