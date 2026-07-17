<script setup>
import teapotIcon from '../assets/img/teapot-icon.png'
</script>

<template>
  <main class="tw:flex-1 tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-8 tw:w-full">
    <div class="tw:flex tw:flex-col tw:items-center tw:justify-center tw:py-24 tw:text-center">
      <div class="tw:mb-6 tw:select-none">
        <img :src="teapotIcon" alt="" class="tw:w-24 tw:h-24 tw:object-contain">
      </div>
      <h1 class="tw:font-serif tw:text-4xl tw:font-bold tw:text-ink-900 tw:mb-3">404</h1>
      <p class="tw:text-gray-500 tw:text-lg tw:mb-2">Страница не найдена</p>
      <p class="tw:text-gray-400 tw:text-sm tw:mb-8 tw:max-w-sm">
        Возможно, адрес изменился или такой страницы никогда не существовало.
      </p>
      <div class="tw:flex tw:items-center tw:gap-4">
        <router-link to="/"
           class="tw:px-5 tw:py-2.5 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors">
          На главную
        </router-link>
        <router-link to="/search"
           class="tw:px-5 tw:py-2.5 tw:border tw:border-clay-200 tw:hover:bg-clay-50 tw:text-ink-800 tw:text-sm tw:rounded-lg tw:transition-colors">
          Поиск
        </router-link>
      </div>
    </div>
  </main>
</template>
