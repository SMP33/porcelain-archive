<script setup>
defineProps({
  pages: { type: Array, required: true },
})
const emit = defineEmits(['open'])
</script>

<template>
  <div class="tw:grid tw:grid-cols-2 tw:sm:grid-cols-3 tw:xl:grid-cols-4 tw:gap-3">
    <button v-for="p in pages" :key="p.page_number" @click="emit('open', p.page_number)"
            class="tw:group tw:relative tw:bg-clay-50 tw:rounded tw:border tw:border-clay-100 tw:overflow-hidden tw:hover:border-clay-300 tw:hover:shadow-md tw:transition-all tw:cursor-zoom-in">
      <img :src="p.thumb_url" :alt="`Страница ${p.page_number}`" loading="lazy"
           class="doc-thumb tw:w-full tw:object-cover tw:group-hover:scale-105 tw:transition-transform tw:duration-300">
      <span class="tw:absolute tw:bottom-1 tw:left-1 tw:bg-black/50 tw:text-white tw:text-xs tw:px-1.5 tw:py-0.5 tw:rounded">
        {{ p.page_number }}
      </span>
    </button>
  </div>
</template>
