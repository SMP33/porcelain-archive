<script setup>
import { ref } from 'vue'
import http from '../api/http'

const name = ref('')
const email = ref('')
const message = ref('')
const fileDescription = ref('')
const fileInput = ref(null)
const selectedFileName = ref('')
const sent = ref(false)
const error = ref('')
const sending = ref(false)

function onFileChange(e) {
  const f = e.target.files[0]
  selectedFileName.value = f ? f.name : ''
}
function clearFile() {
  selectedFileName.value = ''
  fileDescription.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

async function onSubmit() {
  sending.value = true
  error.value = ''
  try {
    const fd = new FormData()
    fd.append('name', name.value)
    fd.append('email', email.value)
    fd.append('message', message.value)
    fd.append('file_description', fileDescription.value)
    const f = fileInput.value?.files?.[0]
    if (f) fd.append('file', f)
    await http.post('/api/ceramic/feedback', fd)
    sent.value = true
  } catch (e) {
    if (e.response?.status === 429) {
      error.value = 'Слишком много сообщений. Попробуйте позже.'
    } else if (e.response?.status === 400 && e.response?.data?.detail) {
      error.value = e.response.data.detail
    } else {
      error.value = 'Не удалось отправить сообщение. Попробуйте позже.'
    }
  } finally {
    sending.value = false
  }
}

function sendAnother() {
  sent.value = false
  name.value = ''
  email.value = ''
  message.value = ''
  clearFile()
}
</script>

<template>
  <main class="tw:flex-1 tw:max-w-6xl tw:mx-auto tw:px-4 tw:py-8 tw:w-full">
  <div class="tw:grid tw:grid-cols-1 tw:md:grid-cols-2 tw:gap-8 tw:md:gap-16 tw:items-start">

    <div>
      <h1 class="tw:font-serif tw:text-3xl tw:font-bold tw:text-ink-900 tw:mb-2">Обратная связь</h1>
      <p class="tw:text-sm tw:text-gray-500 tw:mb-8">
        Напишите нам, если хотите передать документы, исправить ошибку или задать вопрос.
      </p>

      <div v-if="error" class="tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:p-5 tw:mb-6 tw:flex tw:items-start tw:gap-3">
        <span class="tw:text-red-500 tw:text-xl tw:mt-0.5">✕</span>
        <p class="tw:text-red-800 tw:text-sm">{{ error }}</p>
      </div>

      <div v-if="sent" class="tw:bg-green-50 tw:border tw:border-green-200 tw:rounded-lg tw:p-5 tw:flex tw:items-start tw:gap-3">
        <span class="tw:text-green-500 tw:text-xl tw:mt-0.5">✓</span>
        <div>
          <p class="tw:font-medium tw:text-green-800">Сообщение отправлено</p>
          <p class="tw:text-sm tw:text-green-700 tw:mt-1">Спасибо! Мы постараемся ответить в ближайшее время.</p>
          <button type="button" @click="sendAnother" class="tw:inline-block tw:mt-3 tw:text-sm tw:text-green-700 tw:hover:underline">
            ← Отправить ещё одно
          </button>
        </div>
      </div>

      <form v-else @submit.prevent="onSubmit" class="tw:space-y-5">
        <div class="tw:grid tw:grid-cols-1 tw:sm:grid-cols-2 tw:gap-4">
          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">Имя</label>
            <input v-model="name" type="text"
                   class="tw:w-full tw:rounded-lg tw:border tw:border-clay-200 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300 tw:bg-white">
          </div>
          <div>
            <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">
              Email <span class="tw:text-red-400">*</span>
            </label>
            <input v-model="email" type="email" required
                   class="tw:w-full tw:rounded-lg tw:border tw:border-clay-200 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300 tw:bg-white">
          </div>
        </div>
        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">
            Сообщение <span class="tw:text-red-400">*</span>
          </label>
          <textarea v-model="message" rows="6" required
                    class="tw:w-full tw:rounded-lg tw:border tw:border-clay-200 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300 tw:bg-white tw:resize-y"></textarea>
        </div>

        <div>
          <label class="tw:block tw:text-sm tw:font-medium tw:text-gray-700 tw:mb-1">
            Вложение
            <button v-if="selectedFileName" type="button" @click="clearFile"
                    class="tw:ml-2 tw:text-xs tw:font-normal tw:text-gray-400 tw:hover:text-gray-600 tw:transition-colors">Убрать</button>
          </label>
          <div class="tw:rounded-lg tw:border tw:border-dashed tw:border-clay-200 tw:p-4">
            <input ref="fileInput" type="file" @change="onFileChange" class="tw:hidden">
            <div class="tw:flex tw:items-center tw:gap-3">
              <button type="button" @click="fileInput.click()"
                      class="tw:shrink-0 tw:rounded tw:border tw:border-clay-200 tw:bg-clay-50 tw:px-3 tw:py-1.5 tw:text-sm tw:text-clay-700 tw:hover:bg-clay-100 tw:transition-colors">
                Выбрать файл
              </button>
              <span class="tw:text-sm tw:text-gray-500 tw:truncate tw:min-w-0">{{ selectedFileName || 'Файл не выбран' }}</span>
            </div>
            <input v-if="selectedFileName" v-model="fileDescription" type="text" placeholder="Короткое описание файла"
                   class="tw:mt-3 tw:w-full tw:rounded-lg tw:border tw:border-clay-200 tw:px-3 tw:py-2 tw:text-sm tw:focus:outline-none tw:focus:ring-2 tw:focus:ring-clay-300 tw:bg-white">
          </div>
        </div>

        <button type="submit" :disabled="sending"
                class="tw:px-6 tw:py-2.5 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50">
          Отправить
        </button>
      </form>
    </div>

    <div>
      <div class="tw:grid tw:grid-cols-2 tw:gap-3">
        <div class="tw:rounded-xl tw:bg-gray-100 tw:aspect-square tw:flex tw:items-end tw:p-3">
          <span class="tw:text-xs tw:text-gray-300 tw:font-serif tw:tracking-widest">завод</span>
        </div>
        <div class="tw:rounded-xl tw:bg-gray-100 tw:aspect-square tw:flex tw:items-end tw:p-3">
          <span class="tw:text-xs tw:text-gray-300 tw:font-serif tw:tracking-widest">документы</span>
        </div>
        <div class="tw:rounded-xl tw:bg-gray-100 tw:aspect-square tw:flex tw:items-end tw:p-3">
          <span class="tw:text-xs tw:text-gray-300 tw:font-serif tw:tracking-widest">изделия</span>
        </div>
        <div class="tw:rounded-xl tw:bg-gray-100 tw:aspect-square tw:flex tw:items-end tw:p-3">
          <span class="tw:text-xs tw:text-gray-300 tw:font-serif tw:tracking-widest">архив</span>
        </div>
      </div>
    </div>

  </div>
  </main>
</template>
