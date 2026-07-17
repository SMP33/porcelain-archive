<script setup>
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
const isHome = computed(() => route.name === 'home')
</script>

<template>
  <footer class="tw:bg-ink-800 tw:text-clay-100 tw:text-sm tw:mt-auto" :style="isHome ? { scrollSnapAlign: 'start' } : {}">
    <div class="tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-5 tw:flex tw:justify-center">
      <span class="tw:text-white/60 tw:text-sm tw:py-2">Архив документации фарфорных заводов</span>
    </div>
  </footer>
</template>
