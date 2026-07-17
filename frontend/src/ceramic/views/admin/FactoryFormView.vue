<script setup>
import { ref, inject, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '../../api/http'

const props = defineProps({ id: { type: [String, Number], default: null } })
const router = useRouter()
const heading = inject('adminHeading')

const isEdit = computed(() => props.id !== null && props.id !== undefined)

const factory = ref(null)
const name = ref('')
const location = ref('')
const founded = ref('')
const closed = ref('')
const notes = ref('')
const imageFile = ref(null)
const saving = ref(false)

async function load() {
  if (!isEdit.value) {
    heading.value = 'Новый объект'
    return
  }
  const { data } = await http.get(`/api/ceramic/factories/${props.id}`)
  factory.value = data
  name.value = data.name
  location.value = data.location || ''
  founded.value = data.founded || ''
  closed.value = data.closed || ''
  notes.value = data.notes || ''
  heading.value = `Редактировать: ${data.name}`
}
onMounted(load)

function onFileChange(e) {
  imageFile.value = e.target.files[0] || null
}

async function onSubmit() {
  saving.value = true
  try {
    const form = new FormData()
    form.append('name', name.value)
    form.append('location', location.value)
    if (founded.value) form.append('founded', founded.value)
    if (closed.value) form.append('closed', closed.value)
    form.append('notes', notes.value)
    if (imageFile.value) form.append('cover', imageFile.value)

    if (isEdit.value) {
      await http.put(`/api/ceramic/factories/${props.id}`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
    } else {
      await http.post('/api/ceramic/factories', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    }
    router.push('/ceramic/admin/factories')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="tw:max-w-xl">
    <form @submit.prevent="onSubmit" class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6 tw:space-y-5">

      <div>
        <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">
          Название <span class="tw:text-red-400">*</span>
        </label>
        <input v-model="name" type="text" required
               class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
      </div>

      <div>
        <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Местонахождение</label>
        <input v-model="location" type="text" placeholder="Московская обл., г. Ликино-Дулёво"
               class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
      </div>

      <div class="tw:grid tw:grid-cols-2 tw:gap-4">
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Год основания</label>
          <input v-model="founded" type="number" min="1700" max="2100"
                 class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">
            Год закрытия <span class="tw:text-gray-400 tw:font-normal">(если закрыт)</span>
          </label>
          <input v-model="closed" type="number" min="1700" max="2100"
                 class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300">
        </div>
      </div>

      <div>
        <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Примечания</label>
        <textarea v-model="notes" rows="3"
                  class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-red-300 tw:resize-y"></textarea>
      </div>

      <div>
        <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">
          Обложка <span v-if="factory && factory.cover_url" class="tw:text-gray-400 tw:font-normal">(заменить)</span>
        </label>
        <img v-if="factory && factory.cover_url" :src="factory.cover_url"
             class="tw:w-32 tw:h-20 tw:object-cover tw:rounded-lg tw:border tw:border-gray-200 tw:mb-2">
        <input type="file" accept="image/*" @change="onFileChange"
               class="tw:w-full tw:text-sm tw:text-gray-500 tw:file:mr-3 tw:file:py-1.5 tw:file:px-3 tw:file:rounded tw:file:border tw:file:border-gray-200 tw:file:text-xs tw:file:bg-gray-50 tw:file:hover:bg-gray-100 tw:file:transition-colors tw:cursor-pointer">
      </div>

      <div class="tw:flex tw:items-center tw:gap-3 tw:pt-2">
        <button type="submit" :disabled="saving"
                class="tw:px-5 tw:py-2 tw:bg-red-700 tw:hover:bg-red-600 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:transition-colors tw:disabled:opacity-50">
          {{ isEdit ? 'Сохранить' : 'Создать' }}
        </button>
        <router-link to="/ceramic/admin/factories" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors">
          Отмена
        </router-link>
      </div>

    </form>
  </div>
</template>
