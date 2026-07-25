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
        <router-link to="/materials" class="skew-btn skew-btn--nav" :class="{ active: isActive('/materials') }">Материалы</router-link>
        <router-link to="/feedback" class="skew-btn skew-btn--nav" :class="{ active: isActive('/feedback') }">Обратная связь</router-link>

        <!-- Временная кнопка входа в админку (неавторизованного уводит на /admin/login) -->
        <router-link to="/admin/objects" title="Админка" aria-label="Админка"
                     class="tw:ml-2 tw:text-gray-400 tw:border tw:border-gray-200 tw:rounded tw:p-1.5 tw:hover:text-clay-500 tw:hover:border-clay-200 tw:transition-colors"
                     :class="{ 'tw:text-clay-500 tw:border-clay-200': isActive('/admin') }">
          <!-- Человек, входящий в дверь (пиктограмма как на табличках «выход») -->
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"
               stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15.8 3h5v18h-5" stroke-width="1.7" />
            <g stroke-width="2.6">
              <path d="M8.1 6.6 9 11.8" />
              <path d="M9 11.8 11.8 14.4 12.4 18.4" />
              <path d="M9 11.8 6.2 13.8 4.4 17.4" />
              <path d="M8.4 7.8 11.9 9.1" />
              <path d="M8.3 8 5 9.7" />
            </g>
            <circle cx="7.9" cy="3.9" r="2.1" fill="currentColor" stroke="none" />
          </svg>
        </router-link>
      </nav>

    </div>
  </header>
</template>
