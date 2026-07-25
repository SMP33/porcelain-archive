<script setup>
import { ref, inject, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '../../api/http'

const heading = inject('adminHeading')
heading.value = 'Объекты'

const router = useRouter()

const objects = ref([])
const loading = ref(true)
const error = ref('')

const newName = ref('')
const creating = ref(false)

function errorText(err, fallback) {
  return (err.response && err.response.data && err.response.data.detail) || fallback
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await http.get('/api/ceramic/objects')
    objects.value = data.items
  } catch (err) {
    error.value = errorText(err, 'Не удалось загрузить объекты.')
  } finally {
    loading.value = false
  }
}

onMounted(load)

// Объект - обычный документ с указателем document_type=object (см.
// porcelain_archive/ceramic/objects). Создание, страницы, ветки, ревью,
// остальные указатели - как у любого документа, дальше редактируется на
// странице документа (/admin/documents/:id).
async function createObject() {
  const name = newName.value.trim()
  if (!name) return
  creating.value = true
  error.value = ''
  try {
    const { data } = await http.post('/api/documents/create', { name })
    await http.post(`/api/documents/${data.id}/type`, { is_object: true })
    router.push(`/admin/documents/${data.id}`)
  } catch (err) {
    error.value = errorText(err, 'Не удалось создать объект.')
  } finally {
    creating.value = false
  }
}

async function toggleVisibility(o) {
  error.value = ''
  try {
    await http.post(`/api/documents/${o.id}/visibility`, { is_visible: !o.is_visible })
    o.is_visible = !o.is_visible
  } catch (err) {
    error.value = errorText(err, 'Не удалось изменить видимость объекта.')
  }
}
</script>

<template>
  <div class="tw:max-w-3xl tw:space-y-6">

    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
      <h2 class="tw:text-sm tw:font-semibold tw:text-gray-700 tw:mb-3">Новый объект</h2>
      <form @submit.prevent="createObject" class="tw:flex tw:gap-2 tw:max-w-lg">
        <input v-model="newName" type="text" placeholder="Название объекта" required
               class="tw:flex-1 tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
        <button type="submit" :disabled="creating || !newName.trim()"
                class="tw:px-5 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
          {{ creating ? '…' : 'Создать' }}
        </button>
      </form>
      <p class="tw:text-xs tw:text-gray-400 tw:mt-2">
        Создаст документ, пометит его как объект и откроет карточку документа — там же добавляются
        фотографии (страницы) и остальные указатели, как у любого документа.
      </p>
    </div>

    <div v-if="error" class="tw:text-sm tw:text-red-600">{{ error }}</div>

    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
      <table class="tw:w-full tw:text-sm">
        <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
          <tr>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Название</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:sm:table-cell">Указатели</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Фото</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Виден</th>
            <th class="tw:px-4 tw:py-3"></th>
          </tr>
        </thead>
        <tbody class="tw:divide-y tw:divide-gray-100">
          <tr v-for="o in objects" :key="o.id" class="tw:hover:bg-gray-50 tw:transition-colors">
            <td class="tw:px-4 tw:py-3 tw:font-medium tw:text-gray-800">{{ o.name }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:sm:table-cell">
              <span v-if="!o.pointers.length">—</span>
              <span v-for="p in o.pointers" :key="p.pointer"
                    class="tw:inline-block tw:text-xs tw:bg-gray-100 tw:rounded-full tw:px-2 tw:py-0.5 tw:mr-1 tw:mb-1">{{ p.value }}</span>
            </td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:tabular-nums">{{ o.page_count }}</td>
            <td class="tw:px-4 tw:py-3">
              <button type="button" role="switch" :aria-checked="o.is_visible" @click="toggleVisibility(o)"
                      class="tw:relative tw:inline-flex tw:items-center tw:h-5 tw:w-9 tw:rounded-full tw:transition-colors"
                      :class="o.is_visible ? 'tw:bg-red-600' : 'tw:bg-gray-300'">
                <span class="tw:inline-block tw:w-3.5 tw:h-3.5 tw:bg-white tw:rounded-full tw:shadow tw:transform tw:transition-transform"
                      :class="o.is_visible ? 'tw:translate-x-5' : 'tw:translate-x-1'" />
              </button>
            </td>
            <td class="tw:px-4 tw:py-3 tw:text-right">
              <router-link :to="`/admin/documents/${o.id}`"
                 class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors">
                Открыть документ
              </router-link>
            </td>
          </tr>
          <tr v-if="!objects.length && !loading">
            <td colspan="5" class="tw:px-4 tw:py-10 tw:text-center tw:text-gray-400">Объекты не добавлены</td>
          </tr>
        </tbody>
      </table>
    </div>

  </div>
</template>
