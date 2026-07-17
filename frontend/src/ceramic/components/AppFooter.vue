<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import http from '../api/http'

const route = useRoute()
const isHome = computed(() => route.name === 'home')

const email = ref('')
const consent = ref(false)
const status = ref('idle') // idle | sending | done | error

async function onSubmit() {
  status.value = 'sending'
  try {
    await http.post('/api/ceramic/subscribers', { email: email.value })
    status.value = 'done'
  } catch (error) {
    status.value = 'error'
  }
}
</script>

<template>
  <footer class="tw:bg-ink-800 tw:text-clay-100 tw:text-sm tw:mt-auto" :style="isHome ? { scrollSnapAlign: 'start' } : {}">
    <form v-if="status === 'idle' || status === 'sending'" @submit.prevent="onSubmit"
          class="tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-5 tw:flex tw:flex-wrap tw:items-center tw:gap-x-4 tw:gap-y-3 tw:justify-center">
      <span class="tw:text-white tw:font-bold tw:text-base tw:shrink-0">
        👉&nbsp;&nbsp;&nbsp;Подпишитесь на новости проекта
      </span>
      <input v-model="email" type="email" placeholder="email" required
             class="tw:w-72 tw:bg-white/10 tw:border tw:border-white/20 tw:rounded-lg tw:px-3 tw:py-1.5 tw:text-sm tw:text-white tw:placeholder-white/40 tw:focus:outline-none tw:focus:border-white/50">
      <label class="tw:flex tw:items-center tw:gap-2 tw:text-white/50 tw:text-xs tw:cursor-pointer tw:shrink-0">
        <input v-model="consent" type="checkbox" required
               class="tw:w-3.5 tw:h-3.5 tw:accent-red-600 tw:cursor-pointer">
        Даю согласие на обработку персональных данных
      </label>
      <button type="submit" :disabled="status === 'sending'"
              class="tw:shrink-0 tw:px-4 tw:py-1.5 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
        Подписаться
      </button>
    </form>
    <div v-else-if="status === 'done'" class="tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-5 tw:flex tw:justify-center">
      <span class="tw:text-white/80 tw:text-sm tw:py-2">✓ Вы подписаны на новости проекта</span>
    </div>
    <div v-else class="tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-5 tw:flex tw:justify-center">
      <span class="tw:text-red-400 tw:text-sm tw:py-2">Что-то пошло не так, попробуйте позже</span>
    </div>
  </footer>
</template>

