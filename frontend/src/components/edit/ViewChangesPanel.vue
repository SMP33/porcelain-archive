<template>
  <v-card>
    <v-card-title class="text-subtitle-1">Просмотр изменений</v-card-title>
    <v-card-text>
      <v-alert v-if="error" type="error" density="compact">{{ error }}</v-alert>
      <v-row v-else dense>
        <v-col cols="12" md="6">
          <div class="text-subtitle-2 mb-1">Текущий набор изменений (№ {{ branchId }})</div>
          <v-table density="compact" height="400" fixed-header>
            <thead>
              <tr>
                <th>№</th>
                <th>Хеш картинки</th>
                <th>Хеш текста</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="3" class="text-center text-medium-emphasis">Загрузка...</td>
              </tr>
              <tr v-else-if="!branchPages.length">
                <td colspan="3" class="text-center text-medium-emphasis">Страниц пока нет</td>
              </tr>
              <tr v-for="(page, index) in branchPages" :key="index">
                <td>{{ index + 1 }}</td>
                <td class="text-truncate" style="max-width: 160px">{{ page.image_hash || '—' }}</td>
                <td class="text-truncate" style="max-width: 160px">{{ page.text_hash || '—' }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-col>

        <v-col cols="12" md="6">
          <div class="text-subtitle-2 mb-1">master (№ {{ masterBranchId }})</div>
          <v-table density="compact" height="400" fixed-header>
            <thead>
              <tr>
                <th>№</th>
                <th>Хеш картинки</th>
                <th>Хеш текста</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="3" class="text-center text-medium-emphasis">Загрузка...</td>
              </tr>
              <tr v-else-if="!masterPages.length">
                <td colspan="3" class="text-center text-medium-emphasis">Страниц пока нет</td>
              </tr>
              <tr v-for="(page, index) in masterPages" :key="index">
                <td>{{ index + 1 }}</td>
                <td class="text-truncate" style="max-width: 160px">{{ page.image_hash || '—' }}</td>
                <td class="text-truncate" style="max-width: 160px">{{ page.text_hash || '—' }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import http from '../../api/http'

const props = defineProps({
  branchId: { type: [Number, String], required: true },
  masterBranchId: { type: [Number, String], default: null },
})

const branchPages = ref([])
const masterPages = ref([])
const loading = ref(false)
const error = ref('')

const loadPagesHash = async (id) => {
  const response = await http.get(`/api/documents/branches/${id}/pages_hash`)
  return response.data
}

const load = async () => {
  if (!props.branchId || !props.masterBranchId) return

  loading.value = true
  error.value = ''
  try {
    const [branchResult, masterResult] = await Promise.all([
      loadPagesHash(props.branchId),
      loadPagesHash(props.masterBranchId),
    ])
    branchPages.value = branchResult
    masterPages.value = masterResult
  } catch (err) {
    error.value = 'Не удалось загрузить хеши страниц.'
    console.error('Ошибка при получении хешей страниц:', err)
  } finally {
    loading.value = false
  }
}

watch(() => [props.branchId, props.masterBranchId], load, { immediate: true })
</script>
