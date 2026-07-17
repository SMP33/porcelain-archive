<script setup>
defineProps({
  page: { type: Number, required: true },
  pageCount: { type: Number, required: true },
  itemsPerPage: { type: Number, default: null },
  itemsPerPageOptions: { type: Array, default: null },
  total: { type: Number, default: null },
})
defineEmits(['update:page', 'update:itemsPerPage'])
</script>

<template>
  <div class="tw:flex tw:items-center tw:justify-between tw:gap-4 tw:mt-4 tw:text-sm">
    <div v-if="itemsPerPageOptions?.length" class="tw:flex tw:items-center tw:gap-2 tw:text-gray-500">
      <span>Элементов на странице</span>
      <select
        :value="itemsPerPage"
        class="tw:rounded tw:border tw:border-gray-300 tw:px-2 tw:py-1 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"
        @change="$emit('update:itemsPerPage', Number($event.target.value))"
      >
        <option v-for="n in itemsPerPageOptions" :key="n" :value="n">{{ n }}</option>
      </select>
      <span v-if="total !== null">· всего {{ total }}</span>
    </div>
    <div v-else-if="total !== null" class="tw:text-gray-400">всего {{ total }}</div>
    <div v-else />

    <div class="tw:flex tw:items-center tw:gap-2">
      <button
        type="button"
        :disabled="page <= 1"
        class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-clay-200 tw:hover:bg-clay-50 tw:transition-colors tw:disabled:opacity-40 tw:disabled:cursor-not-allowed"
        @click="$emit('update:page', page - 1)"
      >
        ← Назад
      </button>
      <span class="tw:text-gray-500">{{ page }} / {{ pageCount }}</span>
      <button
        type="button"
        :disabled="page >= pageCount"
        class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-clay-200 tw:hover:bg-clay-50 tw:transition-colors tw:disabled:opacity-40 tw:disabled:cursor-not-allowed"
        @click="$emit('update:page', page + 1)"
      >
        Вперёд →
      </button>
    </div>
  </div>
</template>
