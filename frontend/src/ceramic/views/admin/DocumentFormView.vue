<script setup>
import { ref, reactive, inject, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '../../api/http'
import { useAuth } from '../../composables/useAuth'

const props = defineProps({ id: { type: [String, Number], default: null } })
const router = useRouter()
const heading = inject('adminHeading')
const { hasRole } = useAuth()

const isEdit = computed(() => props.id !== null && props.id !== undefined)
const added = ref(false)
const saving = ref(false)
const fullText = ref('')

const factories = ref([])

const DOC_TYPES = ['Приказ', 'Постановление', 'Патент', 'Свидетельство', 'Переписка', 'Протокол', 'Отчёт', 'Акт',
  'Технические условия', 'Справка', 'Инструкция', 'Прейскурант', 'Договор', 'Заявление', 'Другое']
const LANGUAGES = ['Русский', 'Украинский', 'Белорусский', 'Немецкий', 'Английский', 'Французский', 'Польский', 'Чешский', 'Другой']
const AUTHENTICITIES = ['Подлинник', 'Копия', 'Заверенная копия', 'Фотокопия', 'Типографский экземпляр']

const form = reactive({
  factory_id: '', title: '', doc_type: '', doc_date: '', author: '', language: '',
  authenticity: '', geography: '', keywords: '', description: '',
  source_archive: '', fund: '', inventory_no: '', case_no: '', sheets: '',
})

function resetForm() {
  Object.assign(form, {
    factory_id: '', title: '', doc_type: '', doc_date: '', author: '', language: '',
    authenticity: '', geography: '', keywords: '', description: '',
    source_archive: '', fund: '', inventory_no: '', case_no: '', sheets: '',
  })
}

async function loadFactories() {
  const { data } = await http.get('/api/ceramic/factories', { params: { offset: 0, limit: 500 } })
  factories.value = data.items
}

async function load() {
  await loadFactories()
  if (!isEdit.value) {
    heading.value = 'Новый документ'
    return
  }
  const { data } = await http.get(`/api/ceramic/documents/${props.id}`)
  Object.keys(form).forEach((key) => {
    if (data[key] !== undefined && data[key] !== null) form[key] = data[key]
  })
  fullText.value = data.full_text || ''
  heading.value = `Редактировать: ${data.title}`
}
onMounted(load)

async function onSubmit() {
  saving.value = true
  added.value = false
  try {
    const payload = { ...form, factory_id: form.factory_id || null }
    if (isEdit.value) {
      await http.put(`/api/ceramic/documents/${props.id}`, payload)
      router.push('/ceramic/admin/documents')
    } else {
      const { data } = await http.post('/api/ceramic/documents', payload)
      if (hasRole('admin')) {
        router.push(`/ceramic/admin/documents/${data.id}/edit`)
      } else {
        resetForm()
        added.value = true
      }
    }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <div v-if="added" class="tw:mb-5 tw:flex tw:items-center tw:gap-2 tw:bg-green-50 tw:border tw:border-green-200 tw:text-green-800 tw:rounded-xl tw:px-4 tw:py-3 tw:text-sm">
      <span>✓</span> Документ успешно добавлен.
    </div>
    <div class="tw:max-w-2xl">
      <form @submit.prevent="onSubmit" class="tw:space-y-8">

        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6 tw:space-y-5">
          <h2 class="tw:text-sm tw:font-semibold tw:text-gray-500 tw:uppercase tw:tracking-wide">Основное</h2>

          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Объект</label>
            <select v-model="form.factory_id"
                    class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
              <option value="">— не указан —</option>
              <option v-for="f in factories" :key="f.id" :value="f.id">{{ f.name }}</option>
            </select>
          </div>

          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">
              Название <span class="tw:text-red-400">*</span>
            </label>
            <input v-model="form.title" type="text" required
                   class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
          </div>

          <div class="tw:grid tw:grid-cols-2 tw:gap-4">
            <div>
              <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Тип документа</label>
              <input v-model="form.doc_type" type="text" list="doc-types" placeholder="Выберите или введите…"
                     class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
              <datalist id="doc-types">
                <option v-for="t in DOC_TYPES" :key="t" :value="t"></option>
              </datalist>
            </div>
            <div>
              <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Дата</label>
              <input v-model="form.doc_date" type="text" placeholder="1954 или 1954-03-15"
                     pattern="\d{4}(-\d{2}(-\d{2})?)?" title="Формат: ГГГГ или ГГГГ-ММ-ДД"
                     class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
            </div>
          </div>

          <div class="tw:grid tw:grid-cols-2 tw:gap-4">
            <div>
              <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Автор</label>
              <input v-model="form.author" type="text"
                     class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
            </div>
            <div>
              <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Язык</label>
              <select v-model="form.language"
                      class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
                <option value="">— не указан —</option>
                <option v-for="l in LANGUAGES" :key="l" :value="l">{{ l }}</option>
              </select>
            </div>
          </div>

          <div class="tw:grid tw:grid-cols-2 tw:gap-4">
            <div>
              <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Подлинность</label>
              <select v-model="form.authenticity"
                      class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
                <option value="">— не указана —</option>
                <option v-for="a in AUTHENTICITIES" :key="a" :value="a">{{ a }}</option>
              </select>
            </div>
            <div>
              <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">География</label>
              <input v-model="form.geography" type="text" placeholder="Москва, Дулёво, РСФСР"
                     class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
            </div>
          </div>

          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Ключевые слова</label>
            <input v-model="form.keywords" type="text" placeholder="фарфор, ОТК, стандарты — через запятую"
                   class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
          </div>

          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Аннотация</label>
            <textarea v-model="form.description" rows="3"
                      class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300 tw:resize-y"></textarea>
          </div>
        </div>

        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6 tw:space-y-5">
          <h2 class="tw:text-sm tw:font-semibold tw:text-gray-500 tw:uppercase tw:tracking-wide">Архивные реквизиты</h2>

          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Архив</label>
            <input v-model="form.source_archive" type="text" placeholder="РГАЭ, ЦГАЛИ…"
                   class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
          </div>

          <div class="tw:grid tw:grid-cols-3 tw:gap-4">
            <div>
              <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Фонд (ф.)</label>
              <input v-model="form.fund" type="text" placeholder="8543"
                     class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
            </div>
            <div>
              <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Опись (оп.)</label>
              <input v-model="form.inventory_no" type="text" placeholder="1"
                     class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
            </div>
            <div>
              <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Дело (д.)</label>
              <input v-model="form.case_no" type="text" placeholder="12"
                     class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
            </div>
          </div>

          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Листы (лл.)</label>
            <input v-model="form.sheets" type="text" placeholder="лл. 23–45 об."
                   class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
          </div>
        </div>

        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6 tw:space-y-3">
          <div class="tw:flex tw:items-center tw:justify-between">
            <h2 class="tw:text-sm tw:font-semibold tw:text-gray-500 tw:uppercase tw:tracking-wide">Распознанный текст</h2>
            <router-link v-if="isEdit" :to="`/ceramic/admin/documents/${props.id}/pages`" class="tw:text-xs tw:text-red-600 tw:hover:text-red-500 tw:transition-colors">
              Редактировать по страницам →
            </router-link>
          </div>
          <p v-if="fullText" class="tw:text-sm tw:text-gray-600 tw:leading-relaxed tw:whitespace-pre-wrap tw:font-mono tw:max-h-64 tw:overflow-y-auto tw:border tw:border-gray-100 tw:rounded-lg tw:p-3 tw:bg-gray-50">{{ fullText }}</p>
          <p v-else class="tw:text-xs tw:text-gray-400">
            Текст появляется автоматически при загрузке страниц и вычитывается постранично на экране «Страницы».
          </p>
          <p class="tw:text-xs tw:text-gray-400">Собирается из текста страниц и индексируется для полнотекстового поиска.</p>
        </div>

        <div class="tw:flex tw:items-center tw:gap-3">
          <button type="submit" :disabled="saving"
                  class="tw:px-5 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
            {{ isEdit ? 'Сохранить' : 'Создать' }}
          </button>
          <router-link v-if="hasRole('admin')" to="/ceramic/admin/documents" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors">
            Отмена
          </router-link>
        </div>

      </form>
    </div>
  </div>
</template>
