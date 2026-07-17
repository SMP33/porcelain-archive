<script setup>
defineProps({
  lb: { type: Object, required: true },
})
</script>

<template>
  <div v-show="lb.isOpen.value"
       class="tw:fixed tw:inset-0 tw:bg-black/90 tw:z-50 tw:flex tw:items-center tw:justify-center tw:p-4"
       @click="lb.close">
    <div class="tw:relative tw:max-w-5xl tw:max-h-full tw:flex tw:flex-col tw:items-center tw:gap-3" @click.stop>

      <div class="tw:flex tw:items-center tw:gap-3 tw:text-white tw:text-sm tw:flex-wrap tw:justify-center">
        <button @click="lb.shiftPage(-1)" :disabled="!lb.canPrev.value"
                class="tw:px-3 tw:py-1 tw:rounded tw:bg-white/10 tw:hover:bg-white/20 tw:transition-colors tw:disabled:opacity-30">
          ← Назад
        </button>
        <span v-if="lb.current.value">Стр. {{ lb.current.value.page_number }} из {{ lb.total.value }}</span>
        <button @click="lb.shiftPage(1)" :disabled="!lb.canNext.value"
                class="tw:px-3 tw:py-1 tw:rounded tw:bg-white/10 tw:hover:bg-white/20 tw:transition-colors tw:disabled:opacity-30">
          Вперёд →
        </button>

        <!-- Zoom controls -->
        <span class="tw:inline-flex tw:items-center tw:rounded tw:bg-white/10 tw:overflow-hidden">
          <button @click="lb.zoomBy(-0.5)" :disabled="!lb.canZoomOut.value" aria-label="Уменьшить"
                  class="tw:px-3 tw:py-1 tw:hover:bg-white/20 tw:transition-colors tw:disabled:opacity-30 tw:text-base tw:leading-none">−</button>
          <button @click="lb.resetZoom" title="Сбросить масштаб"
                  class="tw:px-2 tw:py-1 tw:hover:bg-white/20 tw:transition-colors tw:tabular-nums tw:min-w-[3.5rem]">
            {{ lb.zoomPercent.value }}%
          </button>
          <button @click="lb.zoomBy(0.5)" :disabled="!lb.canZoomIn.value" aria-label="Увеличить"
                  class="tw:px-3 tw:py-1 tw:hover:bg-white/20 tw:transition-colors tw:disabled:opacity-30 tw:text-base tw:leading-none">+</button>
        </span>

        <a v-if="lb.current.value" :href="lb.current.value.image_url" target="_blank"
           class="tw:px-3 tw:py-1 tw:rounded tw:bg-white/10 tw:hover:bg-white/20 tw:transition-colors">
          Открыть оригинал →
        </a>
        <button @click="lb.close" class="tw:ml-2 tw:px-3 tw:py-1 tw:rounded tw:bg-white/10 tw:hover:bg-white/20 tw:transition-colors">
          ✕ Закрыть
        </button>
      </div>

      <div class="tw:relative tw:flex tw:items-center tw:justify-center">
        <div v-if="lb.loading.value" class="tw:absolute tw:inset-0 tw:flex tw:items-center tw:justify-center">
          <svg class="tw:animate-spin tw:w-10 tw:h-10 tw:text-white/60" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="tw:opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="tw:opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
          </svg>
        </div>
        <img v-if="lb.current.value" :ref="(el) => (lb.imgEl.value = el)"
             :src="lb.current.value.image_url" alt=""
             :style="{ opacity: lb.loading.value ? 0 : 1, transition: 'opacity 0.2s ease, transform 0.05s linear', transformOrigin: 'center center', ...lb.transformStyle.value }"
             class="tw:max-h-[80vh] tw:max-w-full tw:rounded tw:shadow-2xl tw:object-contain"
             @load="lb.onImageLoad"
             @wheel="lb.onWheel"
             @dblclick="lb.onDblclick"
             @mousedown="lb.onMousedown"
             @touchstart="lb.onTouchstart"
             @touchmove="lb.onTouchmove"
             @touchend="lb.onTouchend">
      </div>
    </div>
  </div>
</template>
