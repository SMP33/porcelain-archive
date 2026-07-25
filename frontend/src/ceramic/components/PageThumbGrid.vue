<script setup>
defineProps({
  pages: { type: Array, required: true },
  activeNumber: { type: Number, default: null },
  // Подпись кадра («Страница 3») и пропорции миниатюры
  unit: { type: String, default: 'Страница' },
  aspect: { type: String, default: '3/4' },
})
const emit = defineEmits(['open'])
</script>

<template>
  <div class="tw:grid tw:grid-cols-2 tw:sm:grid-cols-3 tw:xl:grid-cols-4 tw:gap-3">
    <button v-for="p in pages" :key="p.page_number" @click="emit('open', p.page_number)"
            class="tw:group tw:relative tw:bg-clay-50 tw:rounded tw:border tw:overflow-hidden tw:hover:shadow-md tw:transition-all tw:cursor-pointer"
            :class="p.page_number === activeNumber
              ? 'tw:border-clay-500 tw:ring-2 tw:ring-clay-300'
              : 'tw:border-clay-100 tw:hover:border-clay-300'">
      <img :src="p.thumb_url" :alt="`${unit} ${p.page_number}`" loading="lazy" :style="{ aspectRatio: aspect }"
           class="tw:w-full tw:object-cover tw:group-hover:scale-105 tw:transition-transform tw:duration-300">
      <span class="tw:absolute tw:bottom-1 tw:left-1 tw:bg-black/50 tw:text-white tw:text-xs tw:px-1.5 tw:py-0.5 tw:rounded">
        {{ p.page_number }}
      </span>
    </button>
  </div>
</template>
