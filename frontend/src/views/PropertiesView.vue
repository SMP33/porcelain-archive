<template>
  <div class="tw:min-h-screen tw:bg-gray-100">
    <AppToolbar />
    <main class="tw:md:pl-[232px] tw:flex tw:flex-col tw:h-screen">
      <div class="tw:border-b tw:border-gray-200 tw:bg-white tw:px-8 tw:py-4 tw:flex tw:items-center tw:justify-between tw:shrink-0">
        <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">Указатели</h1>
        <button
          v-if="hasRole('admin')"
          type="button"
          class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors"
          @click="openCreatePropertyDialog"
        >
          Добавить указатель
        </button>
      </div>

      <div class="tw:flex-1 tw:min-h-0 tw:px-8 tw:py-6">
        <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:h-full tw:overflow-hidden">
          <AppSplitter>
            <template #left>
              <div v-if="propertiesError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:m-4">
                {{ propertiesError }}
              </div>
              <div v-if="propertiesLoading" class="tw:text-sm tw:text-gray-400 tw:p-4">Загрузка…</div>
              <div v-else-if="!properties.length" class="tw:text-sm tw:text-gray-400 tw:p-4">Указателей пока нет</div>
              <ul v-else class="tw:divide-y tw:divide-gray-100">
                <li
                  v-for="item in properties"
                  :key="item.id"
                  :title="item.description || ''"
                  draggable="true"
                  class="tw:flex tw:items-center tw:justify-between tw:gap-2 tw:px-4 tw:py-2 tw:text-sm tw:cursor-pointer tw:transition-colors"
                  :class="selectedProperty && selectedProperty.id === item.id ? 'tw:bg-clay-50' : 'tw:hover:bg-gray-50'"
                  @click="selectProperty(item)"
                  @dragstart="onDragStart(item)"
                  @dragover.prevent
                  @drop="onDrop(item)"
                >
                  <span class="tw:font-medium tw:text-gray-800">{{ item.title }}</span>
                  <button
                    v-if="hasRole('admin') && !item.in_use"
                    type="button"
                    class="tw:p-1 tw:text-red-500 tw:hover:bg-red-50 tw:rounded tw:transition-colors tw:shrink-0"
                    @click.stop="handleDeleteProperty(item)"
                  >
                    <i class="mdi mdi-delete-outline" />
                  </button>
                </li>
              </ul>
            </template>

            <template #right>
              <div v-if="!selectedProperty" class="tw:text-sm tw:text-gray-400 tw:p-4">
                Выберите указатель слева, чтобы отредактировать его
              </div>
              <div v-else class="tw:p-4">
                <div class="tw:space-y-3">
                  <div v-if="hasRole('admin')">
                    <label class="tw:block tw:text-xs tw:font-medium tw:text-gray-500 tw:mb-1">Указатель</label>
                    <div class="tw:text-sm tw:text-gray-700">{{ selectedProperty.tag }}</div>
                  </div>
                  <div>
                    <label class="tw:block tw:text-xs tw:font-medium tw:text-gray-500 tw:mb-1">Название</label>
                    <div class="tw:flex tw:items-center tw:gap-2">
                      <input
                        v-model="titleForm"
                        type="text"
                        class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"
                      >
                      <button
                        type="button"
                        :disabled="savingTitle || titleForm.trim() === selectedProperty.title"
                        class="tw:px-3 tw:py-2 tw:text-sm tw:font-medium tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:rounded-lg tw:transition-colors tw:disabled:opacity-50 tw:shrink-0"
                        @click="handleSaveTitle"
                      >
                        {{ savingTitle ? '…' : 'Сохранить' }}
                      </button>
                    </div>
                    <div v-if="saveTitleError" class="tw:text-sm tw:text-red-600 tw:mt-1">{{ saveTitleError }}</div>
                  </div>
                  <div v-if="selectedProperty.description">
                    <label class="tw:block tw:text-xs tw:font-medium tw:text-gray-500 tw:mb-1">Описание</label>
                    <div class="tw:text-sm tw:text-gray-600">{{ selectedProperty.description }}</div>
                  </div>
                  <div v-if="hasRole('admin')">
                    <label class="tw:block tw:text-xs tw:font-medium tw:text-gray-500 tw:mb-1">Флаги</label>
                    <div class="tw:flex tw:items-center tw:gap-4 tw:text-sm tw:text-gray-700">
                      <label class="tw:flex tw:items-center tw:gap-1.5">
                        <input v-model="flagsForm.is_list" type="checkbox" :disabled="selectedProperty.is_system"> Список
                      </label>
                      <label class="tw:flex tw:items-center tw:gap-1.5">
                        <input v-model="flagsForm.is_editable" type="checkbox" :disabled="selectedProperty.is_system"> Редактируется
                      </label>
                      <label class="tw:flex tw:items-center tw:gap-1.5">
                        <input v-model="flagsForm.is_visible" type="checkbox" :disabled="selectedProperty.is_system"> Виден
                      </label>
                      <button
                        v-if="!selectedProperty.is_system"
                        type="button"
                        :disabled="savingFlags"
                        class="tw:px-3 tw:py-1.5 tw:text-xs tw:font-medium tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:rounded-lg tw:transition-colors tw:disabled:opacity-50"
                        @click="handleSaveFlags"
                      >
                        {{ savingFlags ? '…' : 'Сохранить' }}
                      </button>
                    </div>
                    <div v-if="selectedProperty.is_system" class="tw:text-xs tw:text-gray-400 tw:mt-1">Системный указатель - флаги менять нельзя</div>
                    <div v-if="saveFlagsError" class="tw:text-sm tw:text-red-600 tw:mt-1">{{ saveFlagsError }}</div>
                  </div>
                </div>

                <div class="tw:flex tw:items-center tw:justify-between tw:mt-6 tw:mb-2 tw:pt-4 tw:border-t tw:border-gray-100">
                  <h3 class="tw:text-sm tw:font-semibold tw:text-gray-700">Допустимые значения</h3>
                  <button
                    type="button"
                    class="tw:px-3 tw:py-1.5 tw:text-xs tw:font-medium tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:rounded-lg tw:transition-colors"
                    @click="openCreateEnumDialog"
                  >
                    Добавить значение
                  </button>
                </div>

                <div v-if="enumError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mb-2">
                  {{ enumError }}
                </div>
                <div v-if="enumLoading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
                <div v-else-if="!enumValues.length" class="tw:text-sm tw:text-gray-400">Значений пока нет</div>
                <ul v-else class="tw:divide-y tw:divide-gray-100 tw:border tw:border-gray-100 tw:rounded-lg">
                  <li v-for="item in enumValues" :key="item.id" class="tw:flex tw:items-center tw:gap-2 tw:px-3 tw:py-2 tw:text-sm">
                    <input
                      :value="item.value"
                      type="text"
                      class="tw:flex-1 tw:min-w-0 tw:bg-transparent tw:border tw:border-transparent tw:hover:border-gray-300 tw:focus:border-clay-400 tw:focus:bg-gray-50 tw:focus:outline-none tw:rounded tw:px-1 tw:py-0.5 tw:text-gray-700"
                      @change="handleUpdateEnumValue(item, $event.target.value)"
                    >
                    <button
                      type="button"
                      class="tw:p-1 tw:text-red-500 tw:hover:bg-red-50 tw:rounded tw:transition-colors tw:shrink-0"
                      @click="handleDeleteEnumValue(item)"
                    >
                      <i class="mdi mdi-delete-outline" />
                    </button>
                  </li>
                </ul>
              </div>
            </template>
          </AppSplitter>
        </div>
      </div>
    </main>

    <AppModal v-model="createPropertyDialogOpen" max-width="tw:max-w-md">
      <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">Новый указатель</h2>
      <div class="tw:space-y-4">
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Указатель</label>
          <input
            v-model="newProperty.tag"
            type="text"
            autofocus
            placeholder="только a-z и _"
            class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"
          >
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Название</label>
          <input v-model="newProperty.title" type="text"
                 class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300">
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Описание</label>
          <textarea v-model="newProperty.description" rows="2"
                    class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"></textarea>
        </div>
        <div class="tw:flex tw:flex-col tw:gap-2">
          <label class="tw:flex tw:items-center tw:gap-2 tw:text-sm tw:text-gray-700">
            <input v-model="newProperty.is_list" type="checkbox"> Список значений
          </label>
          <label class="tw:flex tw:items-center tw:gap-2 tw:text-sm tw:text-gray-700">
            <input v-model="newProperty.is_editable" type="checkbox"> Доступен для редактирования
          </label>
          <label class="tw:flex tw:items-center tw:gap-2 tw:text-sm tw:text-gray-700">
            <input v-model="newProperty.is_visible" type="checkbox"> Виден обычным пользователям
          </label>
        </div>
        <div v-if="createPropertyError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2">
          {{ createPropertyError }}
        </div>
      </div>
      <div class="tw:flex tw:items-center tw:justify-end tw:gap-2 tw:mt-6">
        <button type="button" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors" @click="createPropertyDialogOpen = false">Отмена</button>
        <button
          type="button"
          :disabled="creatingProperty"
          class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
          @click="handleCreateProperty"
        >
          {{ creatingProperty ? 'Создание…' : 'Создать' }}
        </button>
      </div>
    </AppModal>

    <AppModal v-model="createEnumDialogOpen" max-width="tw:max-w-sm">
      <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">Новое значение</h2>
      <input
        v-model="newEnumValue"
        type="text"
        autofocus
        class="tw:w-full tw:rounded-lg tw:border tw:border-gray-300 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300"
        @keyup.enter="handleCreateEnumValue"
      >
      <div v-if="createEnumError" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2 tw:mt-3">
        {{ createEnumError }}
      </div>
      <div class="tw:flex tw:items-center tw:justify-end tw:gap-2 tw:mt-6">
        <button type="button" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors" @click="createEnumDialogOpen = false">Отмена</button>
        <button
          type="button"
          :disabled="creatingEnumValue || !newEnumValue.trim()"
          class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
          @click="handleCreateEnumValue"
        >
          {{ creatingEnumValue ? 'Добавление…' : 'Добавить' }}
        </button>
      </div>
    </AppModal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'
import AppModal from '../components/AppModal.vue'
import AppSplitter from '../components/AppSplitter.vue'

const router = useRouter()
const { hasRole } = useAuth()

const properties = ref([])
const propertiesLoading = ref(true)
const propertiesError = ref('')
let draggedItem = null

const selectedProperty = ref(null)
const titleForm = ref('')
const savingTitle = ref(false)
const saveTitleError = ref('')
const flagsForm = ref({ is_list: false, is_editable: false, is_visible: false })
const savingFlags = ref(false)
const saveFlagsError = ref('')

const enumValues = ref([])
const enumLoading = ref(false)
const enumError = ref('')

const createPropertyDialogOpen = ref(false)
const newProperty = ref({ tag: '', title: '', description: '', is_list: false, is_editable: true, is_visible: false })
const creatingProperty = ref(false)
const createPropertyError = ref('')

const createEnumDialogOpen = ref(false)
const newEnumValue = ref('')
const creatingEnumValue = ref(false)
const createEnumError = ref('')

async function loadProperties() {
  propertiesLoading.value = true
  propertiesError.value = ''
  try {
    const response = await http.get('/api/properties/')
    properties.value = response.data.items
  } catch (err) {
    propertiesError.value = 'Не удалось загрузить указатели.'
    console.error('Ошибка при загрузке указателей:', err)
  } finally {
    propertiesLoading.value = false
  }
}

async function loadEnumValues(propertyId) {
  enumLoading.value = true
  enumError.value = ''
  try {
    const response = await http.get(`/api/properties/${propertyId}/enum`)
    enumValues.value = response.data.items
  } catch (err) {
    enumError.value = 'Не удалось загрузить значения.'
    console.error('Ошибка при загрузке значений указателя:', err)
  } finally {
    enumLoading.value = false
  }
}

function selectProperty(item) {
  selectedProperty.value = item
  titleForm.value = item.title
  flagsForm.value = { is_list: item.is_list, is_editable: item.is_editable, is_visible: item.is_visible }
  saveTitleError.value = ''
  saveFlagsError.value = ''
  loadEnumValues(item.id)
}

function onDragStart(item) {
  draggedItem = item
}

async function onDrop(targetItem) {
  if (!draggedItem || draggedItem.id === targetItem.id) return
  const fromIdx = properties.value.findIndex((p) => p.id === draggedItem.id)
  const toIdx = properties.value.findIndex((p) => p.id === targetItem.id)
  if (fromIdx === -1 || toIdx === -1) return

  const reordered = [...properties.value]
  const [moved] = reordered.splice(fromIdx, 1)
  reordered.splice(toIdx, 0, moved)
  properties.value = reordered
  draggedItem = null

  try {
    await http.post('/api/properties/reorder', { ids: reordered.map((p) => p.id) })
  } catch (err) {
    console.error('Ошибка при изменении порядка указателей:', err)
    await loadProperties()
  }
}

function openCreatePropertyDialog() {
  newProperty.value = { tag: '', title: '', description: '', is_list: false, is_editable: true, is_visible: false }
  createPropertyError.value = ''
  createPropertyDialogOpen.value = true
}

async function handleCreateProperty() {
  if (!newProperty.value.tag.trim() || !newProperty.value.title.trim()) {
    createPropertyError.value = 'Указатель и название обязательны'
    return
  }
  creatingProperty.value = true
  createPropertyError.value = ''
  try {
    await http.post('/api/properties/', newProperty.value)
    createPropertyDialogOpen.value = false
    await loadProperties()
  } catch (err) {
    createPropertyError.value = (err.response && err.response.data && err.response.data.detail) || 'Не удалось создать указатель.'
    console.error('Ошибка при создании указателя:', err)
  } finally {
    creatingProperty.value = false
  }
}

async function handleSaveTitle() {
  if (!selectedProperty.value) return
  savingTitle.value = true
  saveTitleError.value = ''
  try {
    await http.patch(`/api/properties/${selectedProperty.value.id}/title`, { title: titleForm.value })
    selectedProperty.value.title = titleForm.value
    const idx = properties.value.findIndex((p) => p.id === selectedProperty.value.id)
    if (idx !== -1) properties.value[idx].title = titleForm.value
  } catch (err) {
    saveTitleError.value = (err.response && err.response.data && err.response.data.detail) || 'Не удалось сохранить название.'
    console.error('Ошибка при изменении названия указателя:', err)
  } finally {
    savingTitle.value = false
  }
}

async function handleSaveFlags() {
  if (!selectedProperty.value) return
  savingFlags.value = true
  saveFlagsError.value = ''
  try {
    await http.patch(`/api/properties/${selectedProperty.value.id}/flags`, flagsForm.value)
    Object.assign(selectedProperty.value, flagsForm.value)
    const idx = properties.value.findIndex((p) => p.id === selectedProperty.value.id)
    if (idx !== -1) Object.assign(properties.value[idx], flagsForm.value)
  } catch (err) {
    saveFlagsError.value = (err.response && err.response.data && err.response.data.detail) || 'Не удалось сохранить флаги.'
    console.error('Ошибка при изменении флагов указателя:', err)
  } finally {
    savingFlags.value = false
  }
}

async function handleDeleteProperty(item) {
  try {
    await http.delete(`/api/properties/${item.id}`)
    if (selectedProperty.value && selectedProperty.value.id === item.id) {
      selectedProperty.value = null
      enumValues.value = []
    }
    await loadProperties()
  } catch (err) {
    console.error('Ошибка при удалении указателя:', err)
  }
}

function openCreateEnumDialog() {
  newEnumValue.value = ''
  createEnumError.value = ''
  createEnumDialogOpen.value = true
}

async function handleCreateEnumValue() {
  const value = newEnumValue.value.trim()
  if (!value || !selectedProperty.value) return
  creatingEnumValue.value = true
  createEnumError.value = ''
  try {
    await http.post(`/api/properties/${selectedProperty.value.id}/enum`, { value })
    createEnumDialogOpen.value = false
    await loadEnumValues(selectedProperty.value.id)
  } catch (err) {
    createEnumError.value = (err.response && err.response.data && err.response.data.detail) || 'Не удалось добавить значение.'
    console.error('Ошибка при добавлении значения указателя:', err)
  } finally {
    creatingEnumValue.value = false
  }
}

async function handleUpdateEnumValue(item, newValue) {
  const trimmed = newValue.trim()
  if (!trimmed || trimmed === item.value) return
  try {
    await http.patch(`/api/properties/enum/${item.id}`, { value: trimmed })
    item.value = trimmed
  } catch (err) {
    console.error('Ошибка при переименовании значения указателя:', err)
    await loadEnumValues(selectedProperty.value.id)
  }
}

async function handleDeleteEnumValue(item) {
  if (!selectedProperty.value) return
  enumError.value = ''
  try {
    await http.delete(`/api/properties/enum/${item.id}`)
    await loadEnumValues(selectedProperty.value.id)
  } catch (err) {
    enumError.value = (err.response && err.response.data && err.response.data.detail) || 'Не удалось удалить значение.'
    console.error('Ошибка при удалении значения указателя:', err)
  }
}

onMounted(() => {
  if (!hasRole('moderator')) {
    router.push('/edit/access-denied')
    return
  }
  loadProperties()
})
</script>
