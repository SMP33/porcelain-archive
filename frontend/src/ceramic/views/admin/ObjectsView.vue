<script setup>
import { ref, inject, onMounted } from 'vue'
import http from '../../api/http'

const heading = inject('adminHeading')
heading.value = 'Объекты'

const factories = ref([])
const editingId = ref(null)
const saving = ref(false)
const formError = ref('')

const form = ref({ name: '', location: '', founded: '', closed: '', notes: '' })
const coverFile = ref(null)
const currentCover = ref(null)
const removeCover = ref(false)
const fileInput = ref(null)

async function load() {
  const { data } = await http.get('/api/ceramic/factories')
  factories.value = data.items
}
onMounted(load)

function resetForm() {
  editingId.value = null
  form.value = { name: '', location: '', founded: '', closed: '', notes: '' }
  coverFile.value = null
  currentCover.value = null
  removeCover.value = false
  formError.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

function startEdit(f) {
  editingId.value = f.id
  form.value = {
    name: f.name || '',
    location: f.location || '',
    founded: f.founded ?? '',
    closed: f.closed ?? '',
    notes: f.notes || '',
  }
  coverFile.value = null
  currentCover.value = f.cover_url
  removeCover.value = false
  formError.value = ''
  if (fileInput.value) fileInput.value.value = ''
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
}

function onFileChange(e) {
  coverFile.value = e.target.files[0] || null
}

async function save() {
  saving.value = true
  formError.value = ''
  try {
    const fd = new FormData()
    fd.append('name', form.value.name)
    fd.append('location', form.value.location)
    fd.append('founded', form.value.founded === null ? '' : String(form.value.founded))
    fd.append('closed', form.value.closed === null ? '' : String(form.value.closed))
    fd.append('notes', form.value.notes)
    if (coverFile.value) fd.append('cover', coverFile.value)
    if (editingId.value) {
      fd.append('remove_cover', removeCover.value ? 'true' : 'false')
      await http.put(`/api/ceramic/factories/${editingId.value}`, fd)
    } else {
      await http.post('/api/ceramic/factories', fd)
    }
    resetForm()
    await load()
  } catch (err) {
    formError.value = (err.response && err.response.data && err.response.data.detail) || 'Не удалось сохранить объект.'
  } finally {
    saving.value = false
  }
}

async function del(f) {
  if (!confirm(`Удалить объект «${f.name}»? Документы будут отвязаны от него.`)) return
  await http.delete(`/api/ceramic/factories/${f.id}`)
  if (editingId.value === f.id) resetForm()
  await load()
}
</script>

<template>
  <div class="tw:max-w-3xl tw:space-y-6">

    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:overflow-hidden">
      <table class="tw:w-full tw:text-sm">
        <thead class="tw:bg-gray-50 tw:border-b tw:border-gray-200">
          <tr>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Название</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600 tw:hidden tw:sm:table-cell">Местонахождение</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Годы</th>
            <th class="tw:px-4 tw:py-3 tw:text-left tw:font-medium tw:text-gray-600">Док.</th>
            <th class="tw:px-4 tw:py-3"></th>
          </tr>
        </thead>
        <tbody class="tw:divide-y tw:divide-gray-100">
          <tr v-for="f in factories" :key="f.id" class="tw:hover:bg-gray-50 tw:transition-colors">
            <td class="tw:px-4 tw:py-3 tw:font-medium tw:text-gray-800">{{ f.name }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:hidden tw:sm:table-cell">{{ f.location || '—' }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-400 tw:text-xs">{{ f.founded || '?' }} — {{ f.closed || 'н.в.' }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-500">{{ f.doc_count }}</td>
            <td class="tw:px-4 tw:py-3 tw:text-right">
              <div class="tw:flex tw:items-center tw:justify-end tw:gap-2">
                <button @click="startEdit(f)"
                        class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors">
                  Изменить
                </button>
                <button @click="del(f)"
                        class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-red-200 tw:text-red-500 tw:hover:bg-red-50 tw:transition-colors">
                  Удалить
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!factories.length">
            <td colspan="5" class="tw:px-4 tw:py-10 tw:text-center tw:text-gray-400">Объекты не добавлены</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
      <div class="tw:flex tw:items-center tw:justify-between tw:mb-4">
        <h2 class="tw:text-sm tw:font-semibold tw:text-gray-700">{{ editingId ? 'Редактировать объект' : 'Добавить объект' }}</h2>
        <button v-if="editingId" @click="resetForm"
                class="tw:text-xs tw:text-gray-400 tw:hover:text-gray-600 tw:transition-colors">+ Новый объект</button>
      </div>
      <form @submit.prevent="save" class="tw:space-y-4">
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Название</label>
          <input v-model="form.name" type="text" required
                 class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Местонахождение</label>
          <input v-model="form.location" type="text" placeholder="Московская обл., г. Ликино-Дулёво"
                 class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
        </div>
        <div class="tw:grid tw:grid-cols-2 tw:gap-4">
          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Год основания</label>
            <input v-model="form.founded" type="number" min="1700" max="2100"
                   class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
          </div>
          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Год закрытия</label>
            <input v-model="form.closed" type="number" min="1700" max="2100"
                   class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
          </div>
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Примечания</label>
          <textarea v-model="form.notes" rows="3"
                    class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300"></textarea>
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Обложка</label>
          <div v-if="currentCover && !removeCover" class="tw:flex tw:items-center tw:gap-3 tw:mb-2">
            <img :src="currentCover" alt="" class="tw:w-24 tw:h-16 tw:object-cover tw:rounded tw:border tw:border-gray-200">
            <label class="tw:flex tw:items-center tw:gap-2 tw:text-xs tw:text-gray-500 tw:cursor-pointer">
              <input type="checkbox" v-model="removeCover"> Удалить обложку
            </label>
          </div>
          <input ref="fileInput" type="file" accept="image/*" @change="onFileChange"
                 class="tw:block tw:text-sm tw:text-gray-600">
        </div>
        <div v-if="formError" class="tw:text-sm tw:text-red-600">{{ formError }}</div>
        <button type="submit" :disabled="saving"
                class="tw:px-5 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
          {{ saving ? '…' : (editingId ? 'Сохранить' : 'Создать') }}
        </button>
      </form>
    </div>

  </div>
</template>
