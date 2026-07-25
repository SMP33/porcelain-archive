<script setup>
import { ref, inject, onMounted } from 'vue'
import http from '../../api/http'

const heading = inject('adminHeading')
heading.value = 'Документы'

const PAGE_SIZE = 25

const documents = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const error = ref('')

const editingId = ref(null)
const form = ref({ name: '', description: '', date_from: '', date_to: '' })
const saving = ref(false)

const newName = ref('')
const creating = ref(false)

// Указатели: справочник (property + значения) и выбранные значения документа
const properties = ref([])
const selectedPointers = ref([])

function errorText(err, fallback) {
  return (err.response && err.response.data && err.response.data.detail) || fallback
}

async function load() {
  loading.value = true
  try {
    const { data } = await http.get('/api/documents/', {
      params: { offset: (page.value - 1) * PAGE_SIZE, limit: PAGE_SIZE },
    })
    documents.value = data.items
    total.value = data.total
  } catch (err) {
    error.value = errorText(err, 'Не удалось загрузить документы.')
  } finally {
    loading.value = false
  }
}

async function loadProperties() {
  const { data } = await http.get('/api/properties/')
  const items = data.items || []
  properties.value = await Promise.all(
    items.map(async (p) => {
      const { data: enumData } = await http.get(`/api/properties/${p.id}/enum`)
      const values = (enumData.items || []).map((v) => ({ pointer: `${p.tag}:${v.value}`, value: v.value }))
      return { id: p.id, title: p.title, values }
    })
  )
}

onMounted(() => {
  load()
  loadProperties()
})

function goToPage(p) {
  page.value = p
  load()
}

async function createDocument() {
  const name = newName.value.trim()
  if (!name) return
  creating.value = true
  error.value = ''
  try {
    await http.post('/api/documents/create', { name })
    newName.value = ''
    await load()
  } catch (err) {
    error.value = errorText(err, 'Не удалось создать документ.')
  } finally {
    creating.value = false
  }
}

async function startEdit(doc) {
  editingId.value = doc.id
  error.value = ''
  const { data } = await http.get(`/api/documents/${doc.id}`)
  form.value = {
    name: data.name || '',
    description: data.description || '',
    date_from: data.date_from || '',
    date_to: data.date_to || '',
  }
  const { data: props } = await http.get(`/api/documents/${doc.id}/properties`)
  selectedPointers.value = (props.items || []).map((p) => `${p.tag}:${p.value}`)
}

function cancelEdit() {
  editingId.value = null
  selectedPointers.value = []
}

function togglePointer(enumId) {
  const i = selectedPointers.value.indexOf(enumId)
  if (i >= 0) selectedPointers.value.splice(i, 1)
  else selectedPointers.value.push(enumId)
}

async function save(doc) {
  saving.value = true
  error.value = ''
  try {
    if (form.value.name.trim() && form.value.name.trim() !== doc.name) {
      await http.post(`/api/documents/${doc.id}/rename`, { name: form.value.name.trim() })
    }
    await http.post(`/api/documents/${doc.id}/description`, { description: form.value.description })
    await http.post(`/api/documents/${doc.id}/dates`, {
      date_from: form.value.date_from || null,
      date_to: form.value.date_to || null,
    })
    // Указатели сохраняются пакетно: значения группируются по своему указателю
    const byProperty = properties.value
      .map((p) => ({
        property_id: p.id,
        values: p.values.filter((v) => selectedPointers.value.includes(v.pointer)).map((v) => v.value),
      }))
      .filter((entry) => entry.values.length)
    await http.put(`/api/documents/${doc.id}/properties`, { properties: byProperty })
    cancelEdit()
    await load()
  } catch (err) {
    error.value = errorText(err, 'Не удалось сохранить документ.')
  } finally {
    saving.value = false
  }
}

async function toggleVisibility(doc) {
  error.value = ''
  try {
    await http.post(`/api/documents/${doc.id}/visibility`, { is_visible: !doc.is_visible })
    doc.is_visible = !doc.is_visible
  } catch (err) {
    error.value = errorText(err, 'Не удалось изменить видимость документа.')
  }
}

async function del(doc) {
  if (!confirm(`Удалить документ «${doc.name}»? Он пропадёт из списков, файлы и наборы изменений останутся.`)) return
  error.value = ''
  try {
    await http.post(`/api/documents/${doc.id}/delete`)
    if (editingId.value === doc.id) cancelEdit()
    await load()
  } catch (err) {
    error.value = errorText(err, 'Не удалось удалить документ.')
  }
}
</script>

<template>
  <div class="tw:max-w-4xl tw:space-y-6">

    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
      <h2 class="tw:text-sm tw:font-semibold tw:text-gray-700 tw:mb-3">Новый документ</h2>
      <form @submit.prevent="createDocument" class="tw:flex tw:gap-2 tw:max-w-lg">
        <input v-model="newName" type="text" placeholder="Название документа" required
               class="tw:flex-1 tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
        <button type="submit" :disabled="creating || !newName.trim()"
                class="tw:px-5 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
          {{ creating ? '…' : 'Создать' }}
        </button>
      </form>
      <p class="tw:text-xs tw:text-gray-400 tw:mt-2">Страницы загружаются в карточке документа — после создания нажмите «Страницы».</p>
    </div>

    <div v-if="error" class="tw:text-sm tw:text-red-600">{{ error }}</div>

    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
      <table class="tw:w-full tw:text-sm">
        <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
          <tr>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Название</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:sm:table-cell">Автор</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Виден</th>
            <th class="tw:px-4 tw:py-3"></th>
          </tr>
        </thead>
        <tbody class="tw:divide-y tw:divide-gray-100">
          <template v-for="doc in documents" :key="doc.id">
            <tr class="tw:hover:bg-gray-50 tw:transition-colors">
              <td class="tw:px-4 tw:py-3 tw:font-medium tw:text-gray-800">{{ doc.name }}</td>
              <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:sm:table-cell">{{ doc.author || '—' }}</td>
              <td class="tw:px-4 tw:py-3">
                <button type="button" role="switch" :aria-checked="doc.is_visible" @click="toggleVisibility(doc)"
                        class="tw:relative tw:inline-flex tw:items-center tw:h-5 tw:w-9 tw:rounded-full tw:transition-colors"
                        :class="doc.is_visible ? 'tw:bg-red-600' : 'tw:bg-gray-300'">
                  <span class="tw:inline-block tw:w-3.5 tw:h-3.5 tw:bg-white tw:rounded-full tw:shadow tw:transform tw:transition-transform"
                        :class="doc.is_visible ? 'tw:translate-x-5' : 'tw:translate-x-1'" />
                </button>
              </td>
              <td class="tw:px-4 tw:py-3 tw:text-right">
                <div class="tw:flex tw:items-center tw:justify-end tw:gap-2">
                  <router-link :to="`/admin/documents/${doc.id}`"
                     class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors">
                    Страницы
                  </router-link>
                  <button @click="editingId === doc.id ? cancelEdit() : startEdit(doc)"
                          class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors">
                    {{ editingId === doc.id ? 'Свернуть' : 'Изменить' }}
                  </button>
                  <button @click="del(doc)"
                          class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-red-200 tw:text-red-500 tw:hover:bg-red-50 tw:transition-colors">
                    Удалить
                  </button>
                </div>
              </td>
            </tr>

            <tr v-if="editingId === doc.id" class="tw:bg-gray-50">
              <td colspan="4" class="tw:px-4 tw:py-4">
                <div class="tw:space-y-4 tw:max-w-2xl">
                  <div>
                    <label class="tw:block tw:text-xs tw:font-medium tw:text-gray-500 tw:mb-1">Название</label>
                    <input v-model="form.name" type="text"
                           class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
                  </div>
                  <div>
                    <label class="tw:block tw:text-xs tw:font-medium tw:text-gray-500 tw:mb-1">Описание (в карточке и на странице документа)</label>
                    <textarea v-model="form.description" rows="3"
                              class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300"></textarea>
                  </div>
                  <div class="tw:flex tw:gap-4 tw:flex-wrap">
                    <div>
                      <label class="tw:block tw:text-xs tw:font-medium tw:text-gray-500 tw:mb-1">Дата документа</label>
                      <input v-model="form.date_from" type="date"
                             class="tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
                    </div>
                    <div>
                      <label class="tw:block tw:text-xs tw:font-medium tw:text-gray-500 tw:mb-1">Окончание периода (если документ за интервал)</label>
                      <input v-model="form.date_to" type="date"
                             class="tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
                    </div>
                  </div>

                  <div v-if="properties.length">
                    <label class="tw:block tw:text-xs tw:font-medium tw:text-gray-500 tw:mb-2">Указатели</label>
                    <div class="tw:space-y-2">
                      <div v-for="prop in properties" :key="prop.id">
                        <p class="tw:text-xs tw:text-gray-400 tw:uppercase tw:tracking-wider tw:mb-1">{{ prop.title }}</p>
                        <div class="tw:flex tw:flex-wrap tw:gap-2">
                          <button v-for="v in prop.values" :key="v.pointer" type="button" @click="togglePointer(v.pointer)"
                                  class="tw:text-sm tw:rounded-full tw:border tw:px-3 tw:py-1 tw:transition-colors"
                                  :class="selectedPointers.includes(v.pointer)
                                    ? 'tw:bg-red-50 tw:border-red-300 tw:text-red-700'
                                    : 'tw:border-gray-200 tw:text-gray-600 tw:hover:bg-white'">
                            {{ v.value }}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                  <button @click="save(doc)" :disabled="saving"
                          class="tw:px-5 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
                    {{ saving ? '…' : 'Сохранить' }}
                  </button>
                </div>
              </td>
            </tr>
          </template>

          <tr v-if="!documents.length && !loading">
            <td colspan="4" class="tw:px-4 tw:py-10 tw:text-center tw:text-gray-400">Документов пока нет</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="total > PAGE_SIZE" class="tw:flex tw:justify-center tw:items-center tw:gap-3 tw:text-sm">
      <button v-if="page > 1" @click="goToPage(page - 1)"
              class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50">← Назад</button>
      <span class="tw:text-gray-500">{{ page }} / {{ Math.ceil(total / PAGE_SIZE) }}</span>
      <button v-if="page < Math.ceil(total / PAGE_SIZE)" @click="goToPage(page + 1)"
              class="tw:px-3 tw:py-1.5 tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50">Вперёд →</button>
    </div>

  </div>
</template>
