<template>
  <div class="tw:min-h-screen tw:bg-gray-100">
    <AppToolbar />
    <main class="tw:md:pl-[232px]">
      <div class="tw:border-b tw:border-gray-200 tw:bg-white tw:px-8 tw:py-4">
        <div class="tw:flex tw:items-center tw:justify-between tw:gap-4 tw:flex-wrap">
          <h1 class="tw:font-serif tw:text-lg tw:font-semibold tw:text-ink-900">
            <template v-if="branch">
              <router-link :to="`/edit/document/${branch.documentId}`" class="tw:hover:text-clay-500 tw:transition-colors">{{ branch.documentName }}</router-link>
              <span class="tw:text-gray-300 tw:mx-2">/</span>
              <span>Набор изменений № {{ branch.id }}</span>
            </template>
            <template v-else>Редактирование набора изменений</template>
          </h1>

          <div v-if="branch" ref="statusMenuRoot" class="tw:relative tw:inline-block">
            <button
              type="button"
              :disabled="!hasStatusMenuActions"
              class="tw:inline-flex tw:items-center tw:gap-1 tw:px-2 tw:py-0.5 tw:rounded-full tw:text-xs tw:font-medium tw:transition-colors tw:disabled:cursor-default"
              :class="statusBadgeClass(branch.status)"
              @click="statusMenuOpen = !statusMenuOpen"
            >
              {{ statusLabels[branch.status] || branch.status }}
              <i v-if="hasStatusMenuActions" class="mdi mdi-chevron-down" />
            </button>
            <div
              v-if="statusMenuOpen && hasStatusMenuActions"
              class="tw:absolute tw:right-0 tw:z-20 tw:mt-1 tw:min-w-[200px] tw:bg-white tw:rounded-lg tw:border tw:border-gray-200 tw:shadow-lg tw:py-1"
            >
              <template v-if="hasRole('moderator')">
                <button
                  v-if="branch.status === 'to_review' || branch.status === 'in_review'"
                  type="button"
                  class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50 tw:transition-colors"
                  :style="{ color: statusColors.in_work }"
                  @click="statusMenuOpen = false; requestSetStatus('in_work')"
                >
                  Вернуть в работу
                </button>
                <button
                  v-if="branch.status === 'in_work'"
                  type="button"
                  class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50 tw:transition-colors"
                  :style="{ color: statusColors.to_review }"
                  @click="statusMenuOpen = false; requestSetStatus('to_review')"
                >
                  Отправить на проверку
                </button>
                <button
                  v-if="branch.status === 'to_review'"
                  type="button"
                  class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50 tw:transition-colors"
                  :style="{ color: statusColors.in_review }"
                  @click="statusMenuOpen = false; requestSetStatus('in_review')"
                >
                  Взять на проверку
                </button>
                <button
                  v-if="branch.status === 'in_review'"
                  type="button"
                  class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50 tw:transition-colors"
                  :style="{ color: statusColors.in_accept }"
                  @click="statusMenuOpen = false; requestSetStatus('in_accept')"
                >
                  Принять правки
                </button>
                <button
                  v-if="!STATUS_SELECT_LOCKED_STATUSES.includes(branch.status)"
                  type="button"
                  class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-red-50 tw:transition-colors"
                  :style="{ color: statusColors.rejected }"
                  @click="statusMenuOpen = false; requestSetStatus('rejected')"
                >
                  Отклонить
                </button>
              </template>
              <template v-else>
                <button
                  v-if="branch.status === 'in_work'"
                  type="button"
                  class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50 tw:transition-colors"
                  :style="{ color: statusColors.to_review }"
                  @click="statusMenuOpen = false; handleSubmitForReview()"
                >
                  Отправить на проверку
                </button>
                <button
                  v-if="branch.status === 'to_review'"
                  type="button"
                  class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-gray-50 tw:transition-colors"
                  :style="{ color: statusColors.in_work }"
                  @click="statusMenuOpen = false; handleReturnToWork()"
                >
                  Вернуть в работу
                </button>
                <button
                  v-if="branch.status === 'in_work'"
                  type="button"
                  class="tw:block tw:w-full tw:text-left tw:px-3 tw:py-2 tw:text-sm tw:hover:bg-red-50 tw:transition-colors"
                  :style="{ color: statusColors.rejected }"
                  @click="statusMenuOpen = false; requestDeleteBranch()"
                >
                  Удалить
                </button>
              </template>
            </div>
          </div>
        </div>
      </div>
      <div class="tw:px-8 tw:py-6 tw:space-y-4">
        <AppModal v-model="confirmStatusDialog" max-width="tw:max-w-md" :persistent="true" :show-close="false">
          <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">Подтверждение изменения статуса</h2>
          <p class="tw:text-sm tw:text-gray-600">
            Изменить статус набора изменений № {{ branch && branch.id }} на «<span :style="{ color: statusColors[pendingStatus] || 'grey' }">{{ statusLabels[pendingStatus] }}</span>»?
            <template v-if="pendingStatus === 'in_accept'"><br>Изменения будут автоматически слиты в основную версию документа.</template>
          </p>
          <div class="tw:flex tw:items-center tw:justify-end tw:gap-2 tw:mt-6">
            <button type="button" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors" @click="cancelSetStatus">Отмена</button>
            <button
              type="button"
              :disabled="!confirmReady"
              class="tw:px-5 tw:py-2 tw:bg-clay-500 tw:hover:bg-clay-400 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
              @click="confirmSetStatus"
            >
              {{ statusLoading ? 'Сохранение…' : 'Подтвердить' }}
            </button>
          </div>
        </AppModal>

        <AppModal v-model="confirmDeleteDialog" max-width="tw:max-w-md" :persistent="true" :show-close="false">
          <h2 class="tw:font-serif tw:font-bold tw:text-lg tw:text-ink-900 tw:mb-4">Удаление набора изменений</h2>
          <p class="tw:text-sm tw:text-gray-600">
            Удалить набор изменений № {{ branch && branch.id }}? Он перейдёт в статус «Отклонено», редактирование станет недоступно.
          </p>
          <div class="tw:flex tw:items-center tw:justify-end tw:gap-2 tw:mt-6">
            <button type="button" class="tw:px-5 tw:py-2 tw:text-sm tw:text-gray-500 tw:hover:text-gray-700 tw:transition-colors" @click="cancelDeleteBranch">Отмена</button>
            <button
              type="button"
              :disabled="!deleteReady"
              class="tw:px-5 tw:py-2 tw:bg-red-600 tw:hover:bg-red-500 tw:text-white tw:text-sm tw:font-medium tw:rounded-lg tw:shadow-sm tw:transition-colors tw:disabled:opacity-50"
              @click="confirmDeleteBranch"
            >
              {{ deleteLoading ? 'Удаление…' : 'Удалить' }}
            </button>
          </div>
        </AppModal>

        <div v-if="!loading && branch" class="tw:flex tw:flex-col tw:md:flex-row tw:gap-4 tw:items-start">
          <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-2 tw:w-full tw:md:w-56 tw:shrink-0">
            <button
              v-if="!isLocked"
              type="button"
              class="tw:flex tw:items-center tw:gap-2 tw:w-full tw:px-3 tw:py-2 tw:rounded-lg tw:text-sm tw:text-left tw:transition-colors"
              :class="activeView === 'add' ? 'tw:bg-clay-50 tw:text-clay-700' : 'tw:text-gray-600 tw:hover:bg-gray-50'"
              @click="activeView = 'add'"
            >
              <i class="mdi mdi-file-plus" /> Добавить страницы
            </button>
            <button
              v-if="!isLocked"
              type="button"
              class="tw:flex tw:items-center tw:gap-2 tw:w-full tw:px-3 tw:py-2 tw:rounded-lg tw:text-sm tw:text-left tw:transition-colors"
              :class="activeView === 'remove' ? 'tw:bg-clay-50 tw:text-clay-700' : 'tw:text-gray-600 tw:hover:bg-gray-50'"
              @click="activeView = 'remove'"
            >
              <i class="mdi mdi-file-remove" /> Удалить страницы
            </button>
            <button
              v-if="!isLocked"
              type="button"
              class="tw:flex tw:items-center tw:gap-2 tw:w-full tw:px-3 tw:py-2 tw:rounded-lg tw:text-sm tw:text-left tw:transition-colors"
              :class="activeView === 'set_text' ? 'tw:bg-clay-50 tw:text-clay-700' : 'tw:text-gray-600 tw:hover:bg-gray-50'"
              @click="activeView = 'set_text'"
            >
              <i class="mdi mdi-file-pdf-box" /> Задать текст
            </button>
            <button
              v-if="!isLocked"
              type="button"
              class="tw:flex tw:items-center tw:gap-2 tw:w-full tw:px-3 tw:py-2 tw:rounded-lg tw:text-sm tw:text-left tw:transition-colors"
              :class="activeView === 'reset_text' ? 'tw:bg-clay-50 tw:text-clay-700' : 'tw:text-gray-600 tw:hover:bg-gray-50'"
              @click="activeView = 'reset_text'"
            >
              <i class="mdi mdi-text-box-remove" /> Убрать текст
            </button>
            <button
              type="button"
              class="tw:flex tw:items-center tw:gap-2 tw:w-full tw:px-3 tw:py-2 tw:rounded-lg tw:text-sm tw:text-left tw:transition-colors"
              :class="activeView === 'view_changes' ? 'tw:bg-clay-50 tw:text-clay-700' : 'tw:text-gray-600 tw:hover:bg-gray-50'"
              @click="activeView = 'view_changes'"
            >
              <i class="mdi mdi-compare" /> Просмотр изменений
            </button>
          </div>

          <div class="tw:flex-1 tw:w-full tw:space-y-4">
            <AddPagesPanel
              v-if="!isLocked && activeView === 'add'"
              ref="addPagesRef"
              :branch-id="branch.id"
              :page-count="pageCount"
              :allowed-extensions="allowedExtensions"
              @uploaded="onPagesChanged"
            />

            <RemovePagesPanel
              v-if="!isLocked && activeView === 'remove'"
              ref="removePagesRef"
              :branch-id="branch.id"
              :page-count="pageCount"
              @removed="onPagesChanged"
            />

            <SetTextPanel
              v-if="!isLocked && activeView === 'set_text'"
              ref="setTextRef"
              :branch-id="branch.id"
              :page-count="pageCount"
              @submitted="branchTasksRef.reload()"
            />

            <ResetTextPanel
              v-if="!isLocked && activeView === 'reset_text'"
              ref="resetTextRef"
              :branch-id="branch.id"
              :page-count="pageCount"
              @submitted="branchTasksRef.reload()"
            />

            <ViewChangesPanel
              v-if="activeView === 'view_changes'"
              :branch-id="branch.id"
              :initial-commit="branch.initialCommit"
              :last-commit="branch.lastCommit"
            />

            <div class="tw:bg-white tw:rounded-xl tw:border tw:border-gray-200 tw:p-6">
              <h2 class="tw:font-serif tw:font-semibold tw:text-ink-900 tw:mb-4">Страницы</h2>
              <div v-if="!pageCount" class="tw:text-sm tw:text-gray-400">Страниц пока нет</div>
              <div v-else ref="pagesScrollAreaRef" class="pages-scroll-area">
                <div class="tw:grid tw:grid-cols-2 tw:sm:grid-cols-3 tw:md:grid-cols-4 tw:lg:grid-cols-6 tw:gap-3">
                  <div v-for="pos in pageCount" :id="'page-tile-' + pos" :key="pos" class="tw:relative">
                    <div v-if="activeInsertGap === 0 && pos === 1" class="insert-gap-marker insert-gap-marker--left" />
                    <div
                      class="tw:rounded-lg tw:border tw:overflow-hidden tw:cursor-pointer tw:transition-colors"
                      :class="isPageHighlighted(pos) ? highlightClasses[activeHighlightColor] : 'tw:border-gray-200 tw:hover:border-clay-300'"
                      @click="galleryRef.show(pos)"
                    >
                      <img :src="galleryRef && galleryRef.previewImageUrl(pos)" class="tw:w-full tw:h-[120px] tw:object-cover">
                      <div class="tw:text-xs tw:text-gray-500 tw:text-center tw:p-1">{{ pos }}</div>
                    </div>
                    <div v-if="activeInsertGap === pos" class="insert-gap-marker insert-gap-marker--right" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="tw:w-full tw:md:w-64 tw:shrink-0 tw:space-y-4">
            <BranchTasksPanel ref="branchTasksRef" :branch-id="branch.id" />
            <BranchCommentsPanel ref="branchCommentsRef" :branch-id="branch.id" />
          </div>
        </div>

        <PageGalleryViewer
          v-if="branch"
          ref="galleryRef"
          :branch-id="branch.id"
          :page-count="pageCount"
        />

        <div v-if="loading" class="tw:text-sm tw:text-gray-400">Загрузка…</div>
        <div v-if="error" class="tw:text-sm tw:text-red-600 tw:bg-red-50 tw:border tw:border-red-200 tw:rounded-lg tw:px-3 tw:py-2">{{ error }}</div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../api/http'
import { useAuth } from '../composables/useAuth'
import AppToolbar from '../components/AppToolbar.vue'
import AppModal from '../components/AppModal.vue'
import PageGalleryViewer from '../components/PageGalleryViewer.vue'
import AddPagesPanel from '../components/edit/AddPagesPanel.vue'
import RemovePagesPanel from '../components/edit/RemovePagesPanel.vue'
import SetTextPanel from '../components/edit/SetTextPanel.vue'
import ResetTextPanel from '../components/edit/ResetTextPanel.vue'
import ViewChangesPanel from '../components/edit/ViewChangesPanel.vue'
import BranchTasksPanel from '../components/edit/BranchTasksPanel.vue'
import BranchCommentsPanel from '../components/edit/BranchCommentsPanel.vue'

const route = useRoute()
const router = useRouter()
const { user, hasRole } = useAuth()

const statusLabels = {
  in_work: 'В работе',
  to_review: 'Отправлено на проверку',
  in_review: 'Проверяется',
  in_accept: 'Завершение правок',
  accepted: 'Принято',
  rejected: 'Отклонено',
}
const statusColors = {
  in_work: '#6b7280',
  to_review: '#2563eb',
  in_review: '#9333ea',
  in_accept: '#0d9488',
  accepted: '#16a34a',
  rejected: '#dc2626',
}
const statusBadgeClasses = {
  in_work: 'tw:bg-gray-100 tw:text-gray-700',
  to_review: 'tw:bg-blue-100 tw:text-blue-700',
  in_review: 'tw:bg-purple-100 tw:text-purple-700',
  in_accept: 'tw:bg-teal-100 tw:text-teal-700',
  accepted: 'tw:bg-green-100 tw:text-green-700',
  rejected: 'tw:bg-red-100 tw:text-red-700',
}
function statusBadgeClass(status) {
  return statusBadgeClasses[status] || 'tw:bg-gray-100 tw:text-gray-600'
}
const branch = ref(null)
const loading = ref(true)
const error = ref(null)

const pageCount = ref(0)
const allowedExtensions = ref([])

const ACTIVE_VIEW_STORAGE_KEY = 'editView.activeView'
const VALID_VIEWS = ['add', 'remove', 'set_text', 'reset_text', 'view_changes']
const storedActiveView = localStorage.getItem(ACTIVE_VIEW_STORAGE_KEY)
const activeView = ref(VALID_VIEWS.includes(storedActiveView) ? storedActiveView : 'add')

watch(activeView, (value) => {
  localStorage.setItem(ACTIVE_VIEW_STORAGE_KEY, value)
})

const LOCKED_STATUSES = ['to_review', 'in_review', 'accepted', 'rejected', 'in_accept']
// Статусы, при которых комбобокс смены статуса недоступен даже модератору -
// в отличие от LOCKED_STATUSES, "to_review" и "in_review" сюда не входят: именно
// на этих стадиях модератору и нужно менять статус (взять в проверку, принять,
// отклонить, вернуть в работу).
const STATUS_SELECT_LOCKED_STATUSES = ['accepted', 'rejected', 'in_accept']

const statusLoading = ref(false)
const confirmStatusDialog = ref(false)
const pendingStatus = ref(null)
const confirmReady = ref(false)
const CONFIRM_DELAY_MS = 1000
let confirmReadyTimer = null

const deleteLoading = ref(false)
const confirmDeleteDialog = ref(false)
const deleteReady = ref(false)
let deleteReadyTimer = null

const branchTasksRef = ref(null)
const branchCommentsRef = ref(null)
const galleryRef = ref(null)
const addPagesRef = ref(null)
const removePagesRef = ref(null)
const setTextRef = ref(null)
const resetTextRef = ref(null)
const pagesScrollAreaRef = ref(null)

const highlightClasses = {
  red: 'tw:border-2 tw:border-red-400 tw:bg-red-50',
  blue: 'tw:border-2 tw:border-blue-400 tw:bg-blue-50',
  yellow: 'tw:border-2 tw:border-yellow-400 tw:bg-yellow-50',
}

// Диапазон страниц для подсветки плиток - берётся из активной вкладки задачи.
const activeHighlightRange = computed(() => {
  if (activeView.value === 'remove') return removePagesRef.value?.highlightRange ?? null
  if (activeView.value === 'set_text') return setTextRef.value?.highlightRange ?? null
  if (activeView.value === 'reset_text') return resetTextRef.value?.highlightRange ?? null
  return null
})
const activeHighlightColor = computed(() => {
  if (activeView.value === 'remove') return 'red'
  if (activeView.value === 'set_text') return 'blue'
  if (activeView.value === 'reset_text') return 'yellow'
  return null
})
const isPageHighlighted = (pos) => {
  const range = activeHighlightRange.value
  return !!range && pos >= range.start && pos <= range.end
}

// Позиция вставки (0 - перед первой страницей) - подсвечивает границу между
// плитками, куда будут вставлены новые страницы, на вкладке "Добавить страницы".
const activeInsertGap = computed(() => (
  activeView.value === 'add' ? addPagesRef.value?.insertGapPosition ?? null : null
))

// Страница, к которой нужно проскроллить плитки при изменении полей активной вкладки задачи.
// Для "Удалить страницы"/"Убрать текст" зависит от того, какое поле в фокусе
// (начало или конец диапазона) - см. scrollTargetPos в соответствующих панелях.
const scrollTargetPos = computed(() => {
  if (activeView.value === 'add') {
    const gap = activeInsertGap.value
    return gap == null ? null : Math.max(gap, 1)
  }
  if (activeView.value === 'remove') return removePagesRef.value?.scrollTargetPos ?? activeHighlightRange.value?.start ?? null
  if (activeView.value === 'reset_text') return resetTextRef.value?.scrollTargetPos ?? activeHighlightRange.value?.start ?? null
  return activeHighlightRange.value?.start ?? null
})

// Скроллим только контейнер плиток (pagesScrollAreaRef.scrollTop) - el.scrollIntoView()
// затрагивает и скролл всей страницы, чего быть не должно.
watch(scrollTargetPos, (pos) => {
  if (pos == null) return
  nextTick(() => {
    const container = pagesScrollAreaRef.value
    const el = window.document.getElementById('page-tile-' + pos)
    if (!container || !el) return
    const containerRect = container.getBoundingClientRect()
    const elRect = el.getBoundingClientRect()
    if (elRect.top < containerRect.top) {
      container.scrollTop -= containerRect.top - elRect.top
    } else if (elRect.bottom > containerRect.bottom) {
      container.scrollTop += elRect.bottom - containerRect.bottom
    }
  })
})

const isAuthor = computed(() => !!(user.value && branch.value && user.value.id === branch.value.authorId))
const isLocked = computed(() => !!(branch.value && LOCKED_STATUSES.includes(branch.value.status)))

// Меню действий над статусом в шапке страницы - у модератора набор действий
// (произвольная смена статуса вперёд/назад, отклонение), у обычного автора -
// только "Отправить на проверку" / "Вернуть в работу" / "Удалить".
const statusMenuOpen = ref(false)
const statusMenuRoot = ref(null)
const hasUserActions = computed(() => !!(isAuthor.value && branch.value && (branch.value.status === 'in_work' || branch.value.status === 'to_review')))
const hasStatusMenuActions = computed(() => {
  if (!branch.value) return false
  if (hasRole('moderator')) return !STATUS_SELECT_LOCKED_STATUSES.includes(branch.value.status)
  return hasUserActions.value
})

function onStatusMenuDocClick(e) {
  if (statusMenuRoot.value && !statusMenuRoot.value.contains(e.target)) {
    statusMenuOpen.value = false
  }
}

watch(statusMenuOpen, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', onStatusMenuDocClick, true)
  } else {
    document.removeEventListener('click', onStatusMenuDocClick, true)
  }
})

watch(isLocked, (locked) => {
  if (locked && activeView.value !== 'view_changes') {
    activeView.value = 'view_changes'
  }
})

let ws = null
let wsShouldReconnect = true

const loadBranch = async (id) => {
  try {
    const response = await http.get(`/api/documents/branches/${id}`)
    branch.value = {
      id: response.data.id,
      documentId: response.data.document_id,
      documentName: response.data.document_name,
      authorId: response.data.author_id,
      status: response.data.status,
      initialCommit: response.data.initial_commit,
      lastCommit: response.data.last_commit,
    }
  } catch (err) {
    const status = err.response ? err.response.status : null
    if (status === 401) {
      router.push({ name: 'login', query: { redirect: route.fullPath } })
      return
    }
    if (status === 403 || status === 404) {
      router.push('/edit/access-denied')
      return
    }
    error.value = 'Не удалось загрузить набор изменений.'
    console.error('Ошибка при загрузке набора изменений:', err)
  } finally {
    loading.value = false
  }
}

const loadPageCount = async () => {
  try {
    const response = await http.get(`/api/documents/branches/${branch.value.id}/pages/count`)
    pageCount.value = response.data.count
  } catch (err) {
    console.error('Ошибка при получении количества страниц:', err)
  }
}

const loadAllowedExtensions = async () => {
  try {
    const response = await http.get('/api/documents/pages/allowed_extensions')
    allowedExtensions.value = response.data.extensions
  } catch (err) {
    console.error('Ошибка при получении списка допустимых расширений:', err)
  }
}

const handleSubmitForReview = async () => {
  try {
    await http.post(`/api/documents/branches/${branch.value.id}/submit_for_review`, {})
    branch.value.status = 'to_review'
    branchCommentsRef.value.reload()
  } catch (err) {
    console.error('Ошибка при отправке на проверку:', err)
  }
}

const handleReturnToWork = async () => {
  try {
    await http.post(`/api/documents/branches/${branch.value.id}/return_to_work`, {})
    branch.value.status = 'in_work'
    branchCommentsRef.value.reload()
  } catch (err) {
    console.error('Ошибка при возврате в работу:', err)
  }
}

const requestSetStatus = (newStatus) => {
  if (!newStatus || newStatus === branch.value.status) return
  pendingStatus.value = newStatus
  confirmStatusDialog.value = true
  confirmReady.value = false
  clearTimeout(confirmReadyTimer)
  confirmReadyTimer = setTimeout(() => {
    confirmReady.value = true
  }, CONFIRM_DELAY_MS)
}

const cancelSetStatus = () => {
  clearTimeout(confirmReadyTimer)
  confirmStatusDialog.value = false
  pendingStatus.value = null
  confirmReady.value = false
}

const confirmSetStatus = async () => {
  const newStatus = pendingStatus.value
  statusLoading.value = true
  try {
    await http.post(`/api/documents/branches/${branch.value.id}/status`, { status: newStatus })
    branch.value.status = newStatus
    branchTasksRef.value.reload()
    branchCommentsRef.value.reload()
  } catch (err) {
    console.error('Ошибка при изменении статуса:', err)
  } finally {
    statusLoading.value = false
    confirmStatusDialog.value = false
    pendingStatus.value = null
    confirmReady.value = false
  }
}

const requestDeleteBranch = () => {
  confirmDeleteDialog.value = true
  deleteReady.value = false
  clearTimeout(deleteReadyTimer)
  deleteReadyTimer = setTimeout(() => {
    deleteReady.value = true
  }, CONFIRM_DELAY_MS)
}

const cancelDeleteBranch = () => {
  clearTimeout(deleteReadyTimer)
  confirmDeleteDialog.value = false
  deleteReady.value = false
}

const confirmDeleteBranch = async () => {
  deleteLoading.value = true
  try {
    await http.post(`/api/documents/branches/${branch.value.id}/delete`, {})
    branch.value.status = 'rejected'
    branchTasksRef.value.reload()
    branchCommentsRef.value.reload()
  } catch (err) {
    console.error('Ошибка при удалении набора изменений:', err)
  } finally {
    deleteLoading.value = false
    confirmDeleteDialog.value = false
    deleteReady.value = false
  }
}

const onPagesChanged = async () => {
  await loadPageCount()
  branchTasksRef.value.reload()
}

// Тот же WS отдаёт и события задач, и изменения статуса набора изменений -
// на любое сообщение просто перезагружаем текущую ветку и задачи, не разбирая payload.
const connectTaskUpdates = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  ws = new WebSocket(`${protocol}//${window.location.host}/api/tasks/ws`)

  ws.onmessage = async () => {
    branchTasksRef.value.reload()
    branchCommentsRef.value.reload()
    loadPageCount()
    loadBranch(branch.value.id)
  }

  ws.onclose = () => {
    if (wsShouldReconnect) {
      setTimeout(connectTaskUpdates, 2000)
    }
  }
}

onMounted(async () => {
  await loadBranch(route.params.branchId)
  if (branch.value) {
    loadPageCount()
    loadAllowedExtensions()
    connectTaskUpdates()
  }
})

onUnmounted(() => {
  wsShouldReconnect = false
  if (ws) {
    ws.close()
  }
  clearTimeout(confirmReadyTimer)
  clearTimeout(deleteReadyTimer)
  document.removeEventListener('click', onStatusMenuDocClick, true)
})
</script>

<style scoped>
.pages-scroll-area {
  max-height: 660px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 8px;
  scrollbar-width: thin;
  scrollbar-color: rgba(128, 128, 128, 0.3) transparent;
}
.pages-scroll-area::-webkit-scrollbar {
  width: 3px;
}
.pages-scroll-area::-webkit-scrollbar-track {
  background: transparent;
}
.pages-scroll-area::-webkit-scrollbar-thumb {
  background-color: rgba(128, 128, 128, 0.3);
  border-radius: 2px;
}
.insert-gap-marker {
  position: absolute;
  top: 4px;
  bottom: 20px;
  width: 5px;
  border-radius: 3px;
  background-color: #4caf50;
  z-index: 1;
}
.insert-gap-marker--left {
  left: -3px;
}
.insert-gap-marker--right {
  right: -3px;
}
</style>
