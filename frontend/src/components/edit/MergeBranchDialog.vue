<template>
  <v-dialog v-model="dialog" max-width="500">
    <v-card>
      <v-card-title>Завершение правок</v-card-title>
      <v-card-text>
        Завершить правки в наборе изменений № {{ branchId }}? Изменения будут применены к основной версии документа.
        <v-alert v-if="mergeError" type="error" density="compact" class="mt-2">{{ mergeError }}</v-alert>
        <v-alert v-if="mergeSuccess" type="success" density="compact" class="mt-2">
          Задача на завершение правок поставлена в очередь.
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn @click="dialog = false">Закрыть</v-btn>
        <v-btn color="success" :loading="mergingBranch" @click="handleMergeBranch">Завершить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import http from '../../api/http'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
})

const emit = defineEmits(['merged'])

const dialog = ref(false)
const mergingBranch = ref(false)
const mergeError = ref('')
const mergeSuccess = ref(false)

const handleMergeBranch = async () => {
  mergingBranch.value = true
  mergeError.value = ''
  mergeSuccess.value = false
  try {
    await http.post(`/api/documents/branches/${props.branchId}/merge`, {})
    mergeSuccess.value = true
    emit('merged')
  } catch (err) {
    mergeError.value = 'Не удалось поставить слияние в очередь.'
    console.error('Ошибка при слиянии версии документа:', err)
  } finally {
    mergingBranch.value = false
  }
}

const open = () => {
  mergeError.value = ''
  mergeSuccess.value = false
  dialog.value = true
}

defineExpose({ open })
</script>
