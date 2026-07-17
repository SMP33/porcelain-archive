import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { useAuth as useCeramicAuth } from '../ceramic/composables/useAuth'

const routes = [
  // Временная страница-заглушка для ручной проверки после слияния Porcelain и ceramic - удалить, когда будет не нужна.
  { path: '/all-pages', name: 'all-pages', component: () => import('../views/AllPagesView.vue') },
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
  { path: '/', name: 'document-list', component: () => import('../views/DocumentListView.vue') },
  { path: '/branches', name: 'branch-list', component: () => import('../views/BranchListView.vue'), meta: { requiresAuth: true } },
  { path: '/tasks', name: 'task-list', component: () => import('../views/TaskListView.vue'), meta: { requiresAuth: true } },
  { path: '/users', name: 'user-list', component: () => import('../views/UserListView.vue'), meta: { requiresAuth: true } },
  { path: '/server-log', name: 'server-log', component: () => import('../views/ServerLogView.vue'), meta: { requiresAuth: true } },
  { path: '/document/:documentId', name: 'document', component: () => import('../views/DocumentView.vue'), props: true },
  { path: '/edit/:branchId', name: 'edit', component: () => import('../views/EditView.vue'), props: true },
  { path: '/access-denied', name: 'access-denied', component: () => import('../views/AccessDeniedView.vue') },

  // ceramic-factories-archive - вынесено в отдельную ветку /ceramic, чтобы не пересекаться
  // с document/task/user доменами porcelain_archive (свои роуты, свой useAuth).
  {
    path: '/ceramic',
    component: () => import('../ceramic/components/PublicLayout.vue'),
    children: [
      { path: '', name: 'ceramic-home', component: () => import('../ceramic/views/HomeView.vue') },
      { path: 'materials', name: 'ceramic-materials', component: () => import('../ceramic/views/MaterialsView.vue') },
      { path: 'document/:id', name: 'ceramic-document', component: () => import('../ceramic/views/DocumentView.vue'), props: true },
      { path: 'search', name: 'ceramic-search', component: () => import('../ceramic/views/SearchView.vue') },
      { path: 'about', name: 'ceramic-about', component: () => import('../ceramic/views/AboutView.vue') },
      { path: 'feedback', name: 'ceramic-feedback', component: () => import('../ceramic/views/FeedbackView.vue') },
      { path: 'catalog', redirect: '/ceramic/materials' },
      { path: ':pathMatch(.*)*', name: 'ceramic-not-found', component: () => import('../ceramic/views/NotFoundView.vue') },
    ],
  },
  {
    path: '/ceramic/admin/login',
    name: 'ceramic-admin-login',
    component: () => import('../ceramic/views/admin/LoginView.vue'),
  },
  {
    path: '/ceramic/admin',
    component: () => import('../ceramic/components/AdminLayout.vue'),
    meta: { requiresAuth: true, minRole: 'contributor' },
    children: [
      // Документы и заводы (объекты) теперь вне ceramic-админки: документы -
      // общие с porcelain_archive (/, /edit/:branchId), заводы/подписчики удалены.
      { path: '', name: 'ceramic-admin-index', redirect: () => (useCeramicAuth().hasRole('admin') ? '/ceramic/admin/feedback' : '/ceramic') },
      { path: 'feedback', name: 'ceramic-admin-feedback', component: () => import('../ceramic/views/admin/FeedbackView.vue'), meta: { minRole: 'admin' } },
      { path: 'users', name: 'ceramic-admin-users', component: () => import('../ceramic/views/admin/UsersView.vue'), meta: { minRole: 'admin' } },
    ],
  },

  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('../views/NotFoundView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  // Ветка ceramic - своя авторизация (contributor/admin), не связана с useAuth porcelain.
  if (to.path.startsWith('/ceramic')) {
    const { authChecked, user, hasRole, checkAuth } = useCeramicAuth()
    if (!authChecked.value) {
      await checkAuth()
    }
    if (to.meta.requiresAuth && !user.value) {
      return { name: 'ceramic-admin-login', query: { redirect: to.fullPath } }
    }
    if (to.meta.minRole && !hasRole(to.meta.minRole)) {
      return { name: 'ceramic-admin-login', query: { redirect: to.fullPath } }
    }
    return true
  }

  const { authChecked, user, checkAuth } = useAuth()
  if (!authChecked.value) {
    await checkAuth()
  }
  if (to.meta.requiresAuth && !user.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
