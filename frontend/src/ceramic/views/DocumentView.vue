<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import http from '../api/http'
import { useLightbox } from '../composables/useLightbox'
import PageThumbGrid from '../components/PageThumbGrid.vue'
import Lightbox from '../components/Lightbox.vue'

const props = defineProps({ id: { type: [String, Number], required: true } })

const doc = ref(null)
const pages = ref([])
const related = ref([])

// Документы теперь общие с porcelain_archive (document/branch/page) - список
// страниц и картинки берутся из его API (master-ветка документа). Поля вроде
// doc_type/authenticity/geography/keywords/факт привязки к заводу - заглушка
// (null/пусто): в porcelain_archive.document таких полей нет. Текст страниц
// (расшифровка) тоже не подгружается - porcelain отдаёт текст постранично
// блоками для подсветки на картинке, а не готовой строкой на весь документ.
async function load() {
  const { data: docData } = await http.get(`/api/documents/${props.id}`)
  const { data: branchData } = await http.get(`/api/documents/${props.id}/master_branch_id`)
  const branchId = branchData.branch_id
  const { data: countData } = await http.get(`/api/documents/branches/${branchId}/pages/count`)
  const count = countData.count

  doc.value = {
    title: docData.name,
    author: docData.author,
    page_count: count,
    doc_type: null,
    doc_date: null,
    authenticity: null,
    language: null,
    geography: null,
    source_archive: null,
    fund: null,
    inventory_no: null,
    case_no: null,
    sheets: null,
    keywords: null,
    description: null,
  }

  pages.value = Array.from({ length: count }, (_, i) => {
    const pos = i + 1
    return {
      page_number: pos,
      thumb_url: `/api/documents/branches/${branchId}/pages/${pos}/image/preview`,
      image_url: `/api/documents/branches/${branchId}/pages/${pos}/image`,
      ocr_text: null,
    }
  })
  related.value = []
}
onMounted(load)
watch(() => props.id, load)

const textPages = computed(() => pages.value.filter((p) => p.ocr_text))

const pagesRef = computed(() => pages.value)
const lb = useLightbox(pagesRef)

const copiedFor = ref(null)
function copyTranscript(pageNumber, text) {
  navigator.clipboard.writeText(text).then(() => {
    copiedFor.value = pageNumber
    setTimeout(() => {
      if (copiedFor.value === pageNumber) copiedFor.value = null
    }, 1500)
  })
}
</script>

<template>
  <div v-if="doc">
    <div class="tw:border-b tw:border-gray-100">
      <div class="tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-2 tw:text-sm tw:text-gray-500 tw:flex tw:items-center tw:gap-2 tw:flex-wrap">
        <router-link to="/materials" class="tw:hover:text-clay-500 tw:transition-colors">Материалы</router-link>
        <span>›</span>
        <span class="tw:text-ink-800">{{ doc.title }}</span>
      </div>
    </div>

    <main class="tw:flex-1 tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-8 tw:w-full">
      <div class="tw:flex tw:flex-col tw:lg:flex-row tw:gap-8">

        <!-- Sidebar: metadata -->
        <aside class="tw:lg:w-72 tw:xl:w-80 tw:shrink-0">
          <div class="tw:bg-white tw:rounded-xl tw:border tw:border-clay-100 tw:shadow-sm tw:p-5 tw:lg:sticky tw:lg:top-6 tw:space-y-5">

            <h1 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:leading-snug">{{ doc.title }}</h1>

            <dl v-if="doc.doc_type || doc.doc_date || doc.author || doc.authenticity || doc.language || doc.geography || doc.page_count"
                class="tw:space-y-2.5">
              <div v-if="doc.doc_type">
                <dt class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide tw:mb-0.5">Тип</dt>
                <dd class="tw:text-sm tw:text-ink-800">{{ doc.doc_type }}</dd>
              </div>
              <div v-if="doc.doc_date">
                <dt class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide tw:mb-0.5">Дата</dt>
                <dd class="tw:text-sm tw:text-ink-800">{{ doc.doc_date }}</dd>
              </div>
              <div v-if="doc.author">
                <dt class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide tw:mb-0.5">Автор</dt>
                <dd class="tw:text-sm tw:text-ink-800">{{ doc.author }}</dd>
              </div>
              <div v-if="doc.authenticity">
                <dt class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide tw:mb-0.5">Подлинность</dt>
                <dd class="tw:text-sm tw:text-ink-800">{{ doc.authenticity }}</dd>
              </div>
              <div v-if="doc.language">
                <dt class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide tw:mb-0.5">Язык</dt>
                <dd class="tw:text-sm tw:text-ink-800">{{ doc.language }}</dd>
              </div>
              <div v-if="doc.geography">
                <dt class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide tw:mb-0.5">География</dt>
                <dd class="tw:text-sm tw:text-ink-800">{{ doc.geography }}</dd>
              </div>
              <div v-if="doc.page_count">
                <dt class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide tw:mb-0.5">Страниц</dt>
                <dd class="tw:text-sm tw:text-ink-800">{{ doc.page_count }}</dd>
              </div>
            </dl>

            <div v-if="doc.source_archive || doc.fund || doc.inventory_no || doc.case_no || doc.sheets"
                 class="tw:pt-4 tw:border-t tw:border-clay-100">
              <p class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide tw:mb-2">Архив</p>
              <dl class="tw:space-y-1.5 tw:text-sm">
                <div v-if="doc.source_archive" class="tw:font-medium tw:text-ink-800">{{ doc.source_archive }}</div>
                <div v-if="doc.fund || doc.inventory_no || doc.case_no" class="tw:text-gray-500">
                  <template v-if="doc.fund">ф.&nbsp;{{ doc.fund }}</template>
                  <template v-if="doc.inventory_no">&nbsp; оп.&nbsp;{{ doc.inventory_no }}</template>
                  <template v-if="doc.case_no">&nbsp; д.&nbsp;{{ doc.case_no }}</template>
                </div>
                <div v-if="doc.sheets" class="tw:text-gray-500">{{ doc.sheets }}</div>
              </dl>
            </div>

            <div v-if="doc.keywords" class="tw:pt-4 tw:border-t tw:border-clay-100">
              <p class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide tw:mb-2">Ключевые слова</p>
              <div class="tw:flex tw:flex-wrap tw:gap-1.5">
                <router-link v-for="kw in doc.keywords.split(',').map((k) => k.trim()).filter(Boolean)" :key="kw"
                   :to="{ path: '/search', query: { q: kw } }"
                   class="tw:text-xs tw:bg-clay-50 tw:text-clay-600 tw:border tw:border-clay-200 tw:rounded-full tw:px-2.5 tw:py-0.5 tw:hover:bg-clay-100 tw:transition-colors">
                  {{ kw }}
                </router-link>
              </div>
            </div>

            <div v-if="doc.description" class="tw:pt-4 tw:border-t tw:border-clay-100">
              <p class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide tw:mb-1.5">Аннотация</p>
              <p class="tw:text-sm tw:text-gray-600 tw:leading-relaxed">{{ doc.description }}</p>
            </div>

          </div>
        </aside>

        <!-- Pages gallery -->
        <div class="tw:flex-1 tw:min-w-0">
          <template v-if="pages.length">
            <p class="tw:text-sm tw:text-gray-400 tw:mb-4">{{ pages.length }} стр. — нажмите на страницу для просмотра</p>
            <PageThumbGrid :pages="pages" @open="lb.open" />
          </template>
          <div v-else class="tw:flex tw:flex-col tw:items-center tw:justify-center tw:py-24 tw:text-gray-300">
            <svg xmlns="http://www.w3.org/2000/svg" class="tw:w-16 tw:h-16 tw:mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1"
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14
                       M8 6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
            </svg>
            <p class="tw:text-sm">Страницы ещё не загружены</p>
          </div>

          <!-- Расшифровка -->
          <div v-if="textPages.length" class="tw:mt-10">
            <div class="tw:flex tw:items-baseline tw:justify-between tw:mb-1">
              <h2 class="tw:font-serif tw:text-lg tw:font-bold tw:text-ink-900">Расшифровка</h2>
              <span class="tw:text-xs tw:text-gray-400">распознано автоматически, возможны ошибки</span>
            </div>
            <div class="tw:space-y-4 tw:mt-4">
              <div v-for="p in textPages" :key="p.page_number" class="tw:bg-white tw:rounded-xl tw:border tw:border-clay-100 tw:shadow-sm tw:p-4">
                <div class="tw:flex tw:items-center tw:justify-between tw:mb-2">
                  <span class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wide">Страница {{ p.page_number }}</span>
                  <button type="button" @click="copyTranscript(p.page_number, p.ocr_text)"
                          class="tw:text-xs tw:text-clay-500 tw:hover:text-clay-400 tw:transition-colors">
                    {{ copiedFor === p.page_number ? 'Скопировано' : 'Копировать' }}
                  </button>
                </div>
                <p class="tw:text-sm tw:text-ink-800 tw:leading-relaxed tw:whitespace-pre-wrap">{{ p.ocr_text }}</p>
              </div>
            </div>
          </div>

          <div v-if="related.length" class="tw:mt-10">
            <h2 class="tw:font-serif tw:text-lg tw:font-bold tw:text-ink-900 tw:mb-4">Другие документы объекта</h2>
            <div class="tw:grid tw:grid-cols-2 tw:sm:grid-cols-3 tw:gap-3">
              <router-link v-for="r in related" :key="r.id" :to="`/document/${r.id}`"
                 class="tw:group tw:flex tw:items-center tw:gap-3 tw:bg-white tw:border tw:border-clay-100 tw:rounded-xl tw:p-3 tw:hover:border-clay-300 tw:hover:shadow-sm tw:transition-all">
                <div v-if="r.thumb_url" class="tw:shrink-0 tw:w-10 tw:h-14 tw:rounded tw:overflow-hidden tw:bg-clay-50 tw:flex tw:items-center tw:justify-center">
                  <img :src="r.thumb_url" class="tw:w-full tw:h-full tw:object-cover">
                </div>
                <div class="tw:min-w-0">
                  <p class="tw:text-xs tw:font-medium tw:text-ink-800 tw:group-hover:text-clay-500 tw:transition-colors tw:line-clamp-2 tw:leading-snug">{{ r.title }}</p>
                  <p v-if="r.doc_type || r.doc_date" class="tw:text-xs tw:text-gray-400 tw:mt-0.5">
                    {{ r.doc_type || '' }}{{ r.doc_type && r.doc_date ? ', ' : '' }}{{ r.doc_date || '' }}
                  </p>
                </div>
              </router-link>
            </div>
          </div>
        </div>

      </div>
    </main>

    <Lightbox :lb="lb" />
  </div>
</template>
