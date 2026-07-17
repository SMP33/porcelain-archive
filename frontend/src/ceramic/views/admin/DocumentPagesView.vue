<script setup>
import { ref, computed, inject, onMounted } from 'vue'
import http from '../../api/http'
import { useDragReorder } from '../../composables/useDragReorder'

const props = defineProps({ id: { type: [String, Number], required: true } })
const heading = inject('adminHeading')

const docTitle = ref('')
const pages = ref([])
const pageTexts = ref({})
const savingOrder = ref(false)
const savingText = ref(false)
const uploading = ref(false)
const files = ref(null)
const dropActive = ref(false)

async function load() {
  const { data } = await http.get(`/api/ceramic/documents/${props.id}`)
  docTitle.value = data.title
  heading.value = `Страницы: ${data.title}`
  pages.value = data.pages || []
  pageTexts.value = Object.fromEntries(pages.value.map((p) => [p.page_number, p.ocr_text || '']))
  reorder.captureOriginal()
}
onMounted(load)

const reorder = useDragReorder(pages, (p) => p.page_number)

async function saveOrder() {
  savingOrder.value = true
  try {
    const order = pages.value.map((p) => p.page_number)
    await http.put(`/api/ceramic/documents/${props.id}/pages/order`, { order })
    await load()
  } finally {
    savingOrder.value = false
  }
}

async function deletePage(pageNumber) {
  if (!confirm(`Удалить страницу ${pageNumber}?`)) return
  await http.delete(`/api/ceramic/documents/${props.id}/pages/${pageNumber}`)
  await load()
}

async function saveTexts() {
  savingText.value = true
  try {
    await http.put(`/api/ceramic/documents/${props.id}/pages/text`, { pages: pageTexts.value })
    await load()
  } finally {
    savingText.value = false
  }
}

function onFileChange(e) {
  files.value = e.target.files
}
function onDrop(e) {
  dropActive.value = false
  files.value = e.dataTransfer.files
}

async function uploadFiles() {
  if (!files.value || !files.value.length) return
  uploading.value = true
  try {
    const form = new FormData()
    Array.from(files.value).forEach((f) => form.append('files', f))
    await http.post(`/api/ceramic/documents/${props.id}/pages`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
    files.value = null
    await load()
  } finally {
    uploading.value = false
  }
}

const fileCountText = computed(() => (files.value && files.value.length ? `Выбрано: ${files.value.length} файл(а/ов)` : ''))
</script>

<template>
  <div>
    <div class="tw:mb-6 tw:flex tw:items-center tw:gap-3">
      <router-link to="/ceramic/admin/documents" class="tw:text-sm tw:text-gray-400 tw:hover:text-gray-600 tw:transition-colors">← Все документы</router-link>
      <span class="tw:text-gray-300">/</span>
      <span class="tw:text-sm tw:text-gray-500">{{ pages.length }} стр.</span>
    </div>

    <template v-if="pages.length">
      <div v-if="reorder.orderChanged.value" class="tw:mb-4 tw:flex tw:items-center tw:gap-3 tw:bg-amber-50 tw:border tw:border-amber-200 tw:rounded-xl tw:px-4 tw:py-3">
        <span class="tw:text-sm tw:text-amber-800">Порядок страниц изменён</span>
        <button @click="saveOrder" :disabled="savingOrder"
                class="tw:px-4 tw:py-1.5 tw:bg-amber-500 tw:hover:bg-amber-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
          Сохранить порядок
        </button>
        <button @click="load" class="tw:text-sm tw:text-amber-600 tw:hover:text-amber-800 tw:transition-colors">Отмена</button>
      </div>

      <div class="tw:grid tw:grid-cols-2 tw:sm:grid-cols-4 tw:md:grid-cols-6 tw:lg:grid-cols-8 tw:gap-3 tw:mb-8">
        <div v-for="(p, idx) in pages" :key="p.page_number"
             class="page-item tw:group tw:relative tw:cursor-move tw:select-none"
             draggable="true"
             @dragstart="reorder.onDragStart(idx)"
             @dragover.prevent="reorder.onDragOver(idx)"
             @dragend="reorder.onDragEnd"
             :style="{ opacity: reorder.dragSrcIndex.value === idx ? 0.35 : 1 }">
          <a :href="p.image_url" target="_blank" class="tw:block">
            <img :src="p.thumb_url" :alt="`Стр. ${p.page_number}`"
                 class="tw:w-full tw:rounded-lg tw:border tw:border-gray-200 tw:object-cover doc-thumb tw:group-hover:border-red-300 tw:transition-colors tw:pointer-events-none">
          </a>
          <div class="tw:mt-1 tw:flex tw:items-center tw:justify-between tw:px-0.5">
            <span class="tw:text-xs tw:text-gray-400">{{ p.page_number }}</span>
            <button @click="deletePage(p.page_number)"
                    class="tw:text-xs tw:text-red-400 tw:hover:text-red-600 tw:transition-colors tw:opacity-0 tw:group-hover:opacity-100">
              ✕
            </button>
          </div>
        </div>
      </div>

      <!-- Расшифровка по страницам -->
      <form @submit.prevent="saveTexts" class="tw:mb-8">
        <h2 class="tw:text-sm tw:font-semibold tw:text-gray-700 tw:mb-1">Расшифровка по страницам</h2>
        <p class="tw:text-xs tw:text-gray-400 tw:mb-4">
          Заполняется автоматически (OCR) при загрузке. Отредактируйте нужные страницы и сохраните
          все разом — из этих текстов собирается полнотекстовый поиск по документу.
        </p>
        <div class="tw:space-y-4">
          <div v-for="p in pages" :key="p.page_number" class="tw:flex tw:gap-4 tw:items-start tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-4">
            <div class="tw:shrink-0 tw:w-24">
              <a :href="p.image_url" target="_blank">
                <img :src="p.thumb_url" :alt="`Стр. ${p.page_number}`" class="tw:w-full tw:rounded tw:border tw:border-gray-200 tw:hover:border-red-300 tw:transition-colors">
              </a>
              <div class="tw:text-xs tw:text-gray-400 tw:text-center tw:mt-1">Стр. {{ p.page_number }}</div>
            </div>
            <div class="tw:flex-1 tw:min-w-0">
              <textarea v-model="pageTexts[p.page_number]" rows="6"
                        placeholder="Текст страницы. Можно вычитать вручную."
                        class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:font-mono tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300 tw:resize-y"></textarea>
            </div>
          </div>
        </div>
        <div class="tw:mt-4 tw:flex tw:justify-end">
          <button type="submit" :disabled="savingText"
                  class="tw:px-5 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
            Сохранить всё
          </button>
        </div>
      </form>
    </template>
    <div v-else class="tw:text-center tw:py-12 tw:text-gray-400 tw:mb-8">
      <p>Страницы ещё не загружены</p>
    </div>

    <!-- Upload form -->
    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6 tw:max-w-xl">
      <h2 class="tw:text-sm tw:font-semibold tw:text-gray-700 tw:mb-1">Загрузить страницы</h2>
      <p class="tw:text-xs tw:text-gray-400 tw:mb-4">
        JPEG, PNG, TIFF, WebP или PDF. Несколько файлов — сортируются по имени.
        PDF автоматически разбивается на страницы.
      </p>

      <form @submit.prevent="uploadFiles">
        <label class="tw:flex tw:flex-col tw:items-center tw:justify-center tw:w-full tw:h-32 tw:border-2 tw:border-dashed tw:rounded-lg tw:cursor-pointer tw:hover:border-clay-300 tw:hover:bg-clay-50 tw:transition-colors tw:mb-4"
               :class="dropActive ? 'tw:border-clay-400' : 'tw:border-gray-200'"
               @dragover.prevent="dropActive = true" @dragleave="dropActive = false" @drop.prevent="onDrop">
          <span class="tw:text-2xl tw:mb-1">⬆️</span>
          <span class="tw:text-sm tw:text-gray-500">Перетащите файлы или нажмите для выбора</span>
          <span class="tw:text-xs tw:text-gray-400 tw:mt-0.5">{{ fileCountText }}</span>
          <input type="file" multiple accept="image/*,.pdf" class="tw:hidden" @change="onFileChange">
        </label>

        <button type="submit" :disabled="uploading || !files || !files.length"
                class="tw:w-full tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
          {{ uploading ? 'Обрабатываю…' : 'Загрузить' }}
        </button>
      </form>
    </div>
  </div>
</template>
