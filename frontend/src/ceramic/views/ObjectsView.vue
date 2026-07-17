<script setup>
import { ref, onMounted } from 'vue'
import http from '../api/http'
import teapotIcon from '../assets/img/teapot-icon.png'

const factories = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const { data } = await http.get('/api/ceramic/factories', { params: { offset: 0, limit: 200 } })
    factories.value = data.items
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <main class="tw:flex-1 tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-8 tw:w-full">
    <div class="tw:mb-8">
      <h1 class="tw:font-serif tw:text-3xl tw:font-bold tw:text-ink-900 tw:mb-1">Объекты</h1>
    </div>

    <div v-if="factories.length" class="tw:grid tw:grid-cols-1 tw:sm:grid-cols-2 tw:lg:grid-cols-3 tw:gap-5">
      <router-link v-for="f in factories" :key="f.id" :to="`/ceramic/object/${f.id}`"
         class="tw:group tw:bg-white tw:rounded-lg tw:border tw:border-clay-100 tw:shadow-sm tw:hover:shadow-md tw:hover:border-clay-200 tw:transition-all tw:overflow-hidden tw:flex tw:flex-col">

        <div class="tw:relative tw:overflow-hidden tw:bg-gray-100" style="aspect-ratio:16/9">
          <img v-if="f.cover_url" :src="f.cover_url" :alt="f.name"
               class="tw:w-full tw:h-full tw:object-cover tw:group-hover:scale-105 tw:transition-transform tw:duration-300">
          <div v-else class="tw:w-full tw:h-full tw:flex tw:items-center tw:justify-center tw:select-none">
            <img :src="teapotIcon" alt="" class="tw:w-20 tw:h-20 tw:object-contain tw:opacity-25">
          </div>
          <div class="tw:absolute tw:top-1 tw:right-1 tw:w-14 tw:h-14 tw:select-none tw:pointer-events-none">
            <div class="tw:w-full tw:h-full" :style="{
              maskImage: `url(${teapotIcon})`, WebkitMaskImage: `url(${teapotIcon})`,
              maskSize: 'contain', WebkitMaskSize: 'contain',
              maskRepeat: 'no-repeat', WebkitMaskRepeat: 'no-repeat',
              maskPosition: 'center', WebkitMaskPosition: 'center',
              background: 'rgba(0,0,0,0.55)' }"></div>
            <span class="tw:absolute tw:inset-0 tw:flex tw:items-center tw:justify-center tw:text-xs tw:font-bold tw:text-white" style="padding-top: 6px;">
              {{ f.doc_count > 99 ? '99+' : f.doc_count }}
            </span>
          </div>
        </div>

        <div class="tw:p-4 tw:flex tw:flex-col tw:gap-1.5">
          <h2 class="tw:font-serif tw:font-semibold tw:text-base tw:text-ink-900 tw:group-hover:text-clay-500 tw:transition-colors tw:leading-snug">
            {{ f.name }}
          </h2>
          <div v-if="f.location" class="tw:text-sm tw:text-gray-500 tw:flex tw:items-center tw:gap-1">
            <span>📍</span> {{ f.location }}
          </div>
          <div v-if="f.founded || f.closed" class="tw:text-sm tw:text-gray-400">
            {{ f.founded || '?' }} — {{ f.closed || 'н.в.' }}
          </div>
        </div>

      </router-link>
    </div>

    <div v-else-if="!loading" class="tw:text-center tw:py-20 tw:text-gray-300">
      <img :src="teapotIcon" alt="" class="tw:w-16 tw:h-16 tw:mx-auto tw:mb-4 tw:opacity-25">
      <p class="tw:text-lg">Объекты ещё не добавлены</p>
    </div>
  </main>
</template>
