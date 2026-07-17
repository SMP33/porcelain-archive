<script setup>
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMobileMenu } from '../composables/useMobileMenu'
import teapotIcon from '../assets/img/teapot-icon.png'

const route = useRoute()
const { isOpen, toggle, close, bar1Style, bar2Style, bar3Style } = useMobileMenu()

watch(() => route.fullPath, () => close())

function isActive(path) {
  return route.path !== '/' && route.path.startsWith(path)
}
</script>

<template>
  <header class="tw:bg-white tw:border-b tw:border-gray-200 tw:relative tw:z-30 tw:h-16">
    <div class="tw:max-w-6xl tw:mx-auto tw:px-6 tw:h-full tw:flex tw:items-center tw:justify-between">

      <router-link to="/ceramic" class="skew-btn skew-btn--logo tw:font-serif tw:font-bold tw:text-lg tw:leading-tight tw:min-w-0">
        <img :src="teapotIcon" alt="" aria-hidden="true" class="tw:w-8 tw:h-8 tw:shrink-0 tw:object-contain">
        <span class="tw:truncate tw:min-w-0">Архив документации фарфорных заводов</span>
      </router-link>

      <!-- Desktop nav -->
      <nav class="tw:hidden tw:md:flex tw:items-center tw:gap-2">
        <router-link to="/ceramic/materials" class="skew-btn skew-btn--nav" :class="{ active: isActive('/ceramic/materials') }">Материалы</router-link>
        <router-link to="/ceramic/search" class="skew-btn skew-btn--nav" :class="{ active: isActive('/ceramic/search') }">Поиск по материалам</router-link>
        <router-link to="/ceramic/feedback" class="skew-btn skew-btn--nav" :class="{ active: isActive('/ceramic/feedback') }">Обратная связь</router-link>
      </nav>

      <!-- Hamburger button (mobile only) -->
      <button aria-label="Меню" :aria-expanded="isOpen" @click="toggle"
              class="skew-btn skew-btn--nav tw:md:hidden tw:flex tw:flex-col tw:justify-center tw:items-center tw:w-9 tw:h-9 tw:gap-1.5 tw:shrink-0 tw:ml-2">
        <span class="tw:block tw:w-5 tw:h-0.5 tw:bg-ink-800 tw:transition-all tw:duration-200" :style="bar1Style"></span>
        <span class="tw:block tw:w-5 tw:h-0.5 tw:bg-ink-800 tw:transition-all tw:duration-200" :style="bar2Style"></span>
        <span class="tw:block tw:w-5 tw:h-0.5 tw:bg-ink-800 tw:transition-all tw:duration-200" :style="bar3Style"></span>
      </button>

    </div>

    <!-- Mobile dropdown -->
    <div v-show="isOpen" class="tw:md:hidden tw:border-t tw:border-gray-200 tw:bg-white">
      <nav class="tw:max-w-6xl tw:mx-auto tw:px-6 tw:py-3 tw:flex tw:flex-col tw:gap-2 tw:text-sm">
        <router-link to="/ceramic/materials" class="skew-btn skew-btn--nav tw:self-start">Материалы</router-link>
        <router-link to="/ceramic/search" class="skew-btn skew-btn--nav tw:self-start">Поиск по материалам</router-link>
        <router-link to="/ceramic/feedback" class="skew-btn skew-btn--nav tw:self-start">Обратная связь</router-link>
      </nav>
    </div>
  </header>
</template>
