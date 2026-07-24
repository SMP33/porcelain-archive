<script setup>
import { useRoute } from 'vue-router'
import teapotIcon from '../assets/img/teapot-icon.png'

const route = useRoute()

function isActive(path) {
  return route.path !== '/' && route.path.startsWith(path)
}
</script>

<template>
  <header class="tw:bg-white tw:border-b tw:border-gray-200 tw:relative tw:z-30 tw:h-16">
    <div class="tw:max-w-6xl tw:mx-auto tw:px-6 tw:h-full tw:flex tw:items-center tw:justify-between">

      <router-link to="/" class="skew-btn skew-btn--logo tw:font-serif tw:font-bold tw:text-lg tw:leading-tight tw:min-w-0">
        <img :src="teapotIcon" alt="" aria-hidden="true" class="tw:w-8 tw:h-8 tw:shrink-0 tw:object-contain">
        <span class="tw:truncate tw:min-w-0">Архив документации фарфоровых заводов</span>
      </router-link>

      <nav class="tw:flex tw:items-center tw:gap-2">
        <router-link to="/objects" class="skew-btn skew-btn--nav" :class="{ active: isActive('/objects') }">Объекты</router-link>
        <router-link to="/search" class="skew-btn skew-btn--nav" :class="{ active: isActive('/search') }">Поиск по материалам</router-link>
        <router-link to="/feedback" class="skew-btn skew-btn--nav" :class="{ active: isActive('/feedback') }">Обратная связь</router-link>
      </nav>

    </div>
  </header>
</template>
