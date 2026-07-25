<script setup>
import { ref, inject, onMounted } from 'vue'
import http from '../../api/http'

const heading = inject('adminHeading')
heading.value = 'Объекты'

const objects = ref([])
const properties = ref([])
const editingId = ref(null)
const saving = ref(false)
const formError = ref('')

const form = ref({ name: '', notes: '', is_visible: true })
const selectedPointers = ref([])
const images = ref([])          // фотографии редактируемого объекта
const newFiles = ref([])        // файлы для нового объекта (загружаются вместе с ним)
const fileInput = ref(null)

async function load() {
  const { data } = await http.get('/api/ceramic/objects')
  objects.value = data.items
}

async function loadPointers() {
  const { data } = await http.get('/api/ceramic/objects/pointers')
  properties.value = data.properties
}

onMounted(() => {
  load()
  loadPointers()
})

function resetForm() {
  editingId.value = null
  form.value = { name: '', notes: '', is_visible: true }
  selectedPointers.value = []
  images.value = []
  newFiles.value = []
  formError.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

function startEdit(o) {
  editingId.value = o.id
  form.value = { name: o.name || '', notes: o.notes || '', is_visible: o.is_visible !== false }
  selectedPointers.value = o.pointers.map((p) => p.enum_id)
  images.value = [...o.images]
  newFiles.value = []
  formError.value = ''
  if (fileInput.value) fileInput.value.value = ''
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
}

function togglePointer(enumId) {
  const i = selectedPointers.value.indexOf(enumId)
  if (i >= 0) selectedPointers.value.splice(i, 1)
  else selectedPointers.value.push(enumId)
}

async function onFileChange(e) {
  const files = [...e.target.files]
  if (!files.length) return
  if (!editingId.value) {
    newFiles.value = files
    return
  }
  formError.value = ''
  try {
    const fd = new FormData()
    files.forEach((f) => fd.append('images', f))
    const { data } = await http.post(`/api/ceramic/objects/${editingId.value}/images`, fd)
    images.value = data.images
    await load()
  } catch (err) {
    formError.value = errorText(err, 'Не удалось загрузить фотографии.')
  } finally {
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function deleteImage(img) {
  if (!confirm('Удалить фотографию?')) return
  await http.delete(`/api/ceramic/objects/${editingId.value}/images/${img.id}`)
  images.value = images.value.filter((i) => i.id !== img.id)
  await load()
}

async function applyOrder(next) {
  images.value = next
  await http.put(`/api/ceramic/objects/${editingId.value}/images/order`, {
    image_ids: next.map((i) => i.id),
  })
  await load()
}

function moveImage(index, delta) {
  const next = [...images.value]
  const target = index + delta
  if (target < 0 || target >= next.length) return
  ;[next[index], next[target]] = [next[target], next[index]]
  applyOrder(next)
}

function makeCover(index) {
  const next = [...images.value]
  next.unshift(next.splice(index, 1)[0])
  applyOrder(next)
}

function errorText(err, fallback) {
  return (err.response && err.response.data && err.response.data.detail) || fallback
}

async function save() {
  saving.value = true
  formError.value = ''
  try {
    const fd = new FormData()
    fd.append('name', form.value.name)
    fd.append('notes', form.value.notes)
    fd.append('is_visible', form.value.is_visible ? 'true' : 'false')
    selectedPointers.value.forEach((id) => fd.append('pointer', id))
    if (editingId.value) {
      await http.put(`/api/ceramic/objects/${editingId.value}`, fd)
    } else {
      newFiles.value.forEach((f) => fd.append('images', f))
      await http.post('/api/ceramic/objects', fd)
    }
    resetForm()
    await load()
  } catch (err) {
    formError.value = errorText(err, 'Не удалось сохранить объект.')
  } finally {
    saving.value = false
  }
}

async function toggleVisibility(o) {
  const fd = new FormData()
  fd.append('name', o.name)
  fd.append('notes', o.notes || '')
  fd.append('is_visible', o.is_visible ? 'false' : 'true')
  o.pointers.forEach((p) => fd.append('pointer', p.enum_id))
  await http.put(`/api/ceramic/objects/${o.id}`, fd)
  o.is_visible = !o.is_visible
  if (editingId.value === o.id) form.value.is_visible = o.is_visible
}

async function del(o) {
  if (!confirm(`Удалить объект «${o.name}»?`)) return
  await http.delete(`/api/ceramic/objects/${o.id}`)
  if (editingId.value === o.id) resetForm()
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
              <span v-for="p in o.pointers" :key="p.enum_id"
                    class="tw:inline-block tw:text-xs tw:bg-gray-100 tw:rounded-full tw:px-2 tw:py-0.5 tw:mr-1 tw:mb-1">{{ p.value }}</span>
            </td>
            <td class="tw:px-4 tw:py-3 tw:text-gray-500 tw:tabular-nums">{{ o.images.length }}</td>
            <td class="tw:px-4 tw:py-3">
              <button type="button" role="switch" :aria-checked="o.is_visible" @click="toggleVisibility(o)"
                      class="tw:relative tw:inline-flex tw:items-center tw:h-5 tw:w-9 tw:rounded-full tw:transition-colors"
                      :class="o.is_visible ? 'tw:bg-red-600' : 'tw:bg-gray-300'">
                <span class="tw:inline-block tw:w-3.5 tw:h-3.5 tw:bg-white tw:rounded-full tw:shadow tw:transform tw:transition-transform"
                      :class="o.is_visible ? 'tw:translate-x-5' : 'tw:translate-x-1'" />
              </button>
            </td>
            <td class="tw:px-4 tw:py-3 tw:text-right">
              <div class="tw:flex tw:items-center tw:justify-end tw:gap-2">
                <button @click="startEdit(o)"
                        class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:transition-colors">
                  Изменить
                </button>
                <button @click="del(o)"
                        class="tw:px-3 tw:py-1 tw:text-xs tw:rounded tw:border tw:border-red-200 tw:text-red-500 tw:hover:bg-red-50 tw:transition-colors">
                  Удалить
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!objects.length">
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
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Описание</label>
          <textarea v-model="form.notes" rows="4"
                    class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300"></textarea>
        </div>

        <label class="tw:flex tw:items-center tw:gap-2 tw:text-sm tw:text-gray-700">
          <input type="checkbox" v-model="form.is_visible">
          Виден посетителям сайта
        </label>

        <div v-if="properties.length">
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-2">Указатели</label>
          <div class="tw:space-y-3">
            <div v-for="prop in properties" :key="prop.id">
              <p class="tw:text-xs tw:font-semibold tw:text-gray-400 tw:uppercase tw:tracking-wider tw:mb-1">{{ prop.title }}</p>
              <div class="tw:flex tw:flex-wrap tw:gap-2">
                <button v-for="v in prop.values" :key="v.enum_id" type="button" @click="togglePointer(v.enum_id)"
                        class="tw:text-sm tw:rounded-full tw:border tw:px-3 tw:py-1 tw:transition-colors"
                        :class="selectedPointers.includes(v.enum_id)
                          ? 'tw:bg-red-50 tw:border-red-300 tw:text-red-700'
                          : 'tw:border-gray-200 tw:text-gray-600 tw:hover:bg-gray-50'">
                  {{ v.value }}
                </button>
              </div>
            </div>
          </div>
        </div>
        <p v-else class="tw:text-xs tw:text-gray-400">
          Указателей пока нет — их значения создаются в разделе «Указатели» админки архива.
        </p>

        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Фотографии</label>

          <div v-if="editingId && images.length" class="tw:grid tw:grid-cols-4 tw:gap-3 tw:mb-3">
            <div v-for="(img, i) in images" :key="img.id" class="tw:relative">
              <img :src="img.url" alt="" class="tw:w-full tw:h-24 tw:object-cover tw:rounded tw:border tw:border-gray-200">
              <span v-if="i === 0"
                    class="tw:absolute tw:top-1 tw:left-1 tw:text-[0.65rem] tw:bg-black/60 tw:text-white tw:rounded tw:px-1.5 tw:py-0.5">обложка</span>
              <div class="tw:flex tw:items-center tw:justify-between tw:gap-1 tw:mt-1">
                <div class="tw:flex tw:gap-1">
                  <button type="button" @click="moveImage(i, -1)" :disabled="i === 0" title="Левее"
                          class="tw:px-1.5 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:disabled:opacity-30">←</button>
                  <button type="button" @click="moveImage(i, 1)" :disabled="i === images.length - 1" title="Правее"
                          class="tw:px-1.5 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:disabled:opacity-30">→</button>
                  <button type="button" @click="makeCover(i)" :disabled="i === 0" title="Сделать обложкой"
                          class="tw:px-1.5 tw:text-xs tw:rounded tw:border tw:border-gray-200 tw:hover:bg-gray-50 tw:disabled:opacity-30">★</button>
                </div>
                <button type="button" @click="deleteImage(img)" title="Удалить"
                        class="tw:px-1.5 tw:text-xs tw:rounded tw:border tw:border-red-200 tw:text-red-500 tw:hover:bg-red-50">✕</button>
              </div>
            </div>
          </div>

          <input ref="fileInput" type="file" accept="image/*" multiple @change="onFileChange"
                 class="tw:block tw:text-sm tw:text-gray-600">
          <p class="tw:text-xs tw:text-gray-400 tw:mt-1">
            {{ editingId ? 'Выбранные файлы добавляются в галерею сразу.' : 'Файлы загрузятся вместе с созданием объекта.' }}
          </p>
          <p v-if="!editingId && newFiles.length" class="tw:text-xs tw:text-gray-500 tw:mt-1">
            Выбрано файлов: {{ newFiles.length }}
          </p>
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
