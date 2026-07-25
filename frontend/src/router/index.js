import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../ceramic/composables/useAuth'

const routes = [
  // ceramic-factories-archive - основной сайт на корневом домене (свои роуты, свой useAuth).
  {
    path: '/',
    component: () => import('../ceramic/components/PublicLayout.vue'),
    children: [
      { path: '', name: 'ceramic-home', component: () => import('../ceramic/views/HomeView.vue') },

      { path: 'objects', name: 'ceramic-objects', component: () => import('../ceramic/views/ObjectsView.vue') },
      { path: 'objects/:id', name: 'ceramic-object', component: () => import('../ceramic/views/ObjectView.vue'), props: true },
      { path: 'document/:id', name: 'ceramic-document', component: () => import('../ceramic/views/DocumentView.vue'), props: true },
      { path: 'materials', name: 'ceramic-materials', component: () => import('../ceramic/views/SearchView.vue') },
      { path: 'search', redirect: '/materials' },
      { path: 'about', name: 'ceramic-about', component: () => import('../ceramic/views/AboutView.vue') },
      { path: 'feedback', name: 'ceramic-feedback', component: () => import('../ceramic/views/FeedbackView.vue') },
      { path: 'privacy', name: 'ceramic-privacy', component: () => import('../ceramic/views/PrivacyView.vue') },
      { path: 'catalog', redirect: '/materials' },
      { path: ':pathMatch(.*)*', name: 'ceramic-not-found', component: () => import('../ceramic/views/NotFoundView.vue') },
    ],
  },
  {
    path: '/admin/login',
    name: 'ceramic-admin-login',
    component: () => import('../ceramic/views/admin/LoginView.vue'),
  },
  {
    path: '/admin',
    component: () => import('../ceramic/components/AdminLayout.vue'),
    meta: { requiresAuth: true, minRole: 'contributor' },
    children: [
      // Вся работа с архивом (документы, наборы изменений, задачи, указатели)
      // перенесена сюда из /edit - отдельного раздела больше нет.
      { path: '', name: 'ceramic-admin-index', redirect: () => (useAuth().hasRole('moderator') ? '/admin/documents' : '/admin/branches') },
      { path: 'feedback', name: 'ceramic-admin-feedback', component: () => import('../ceramic/views/admin/FeedbackView.vue'), meta: { minRole: 'admin' } },
      { path: 'subscribers', name: 'ceramic-admin-subscribers', component: () => import('../ceramic/views/admin/SubscribersView.vue'), meta: { minRole: 'admin' } },
      { path: 'objects', name: 'ceramic-admin-objects', component: () => import('../ceramic/views/admin/ObjectsView.vue'), meta: { minRole: 'admin' } },
      { path: 'users', name: 'ceramic-admin-users', component: () => import('../ceramic/views/admin/UsersView.vue'), meta: { minRole: 'admin' } },

      { path: 'documents', name: 'ceramic-admin-documents', component: () => import('../ceramic/views/admin/DocumentsView.vue'), meta: { minRole: 'moderator' } },
      { path: 'documents/:documentId', name: 'ceramic-admin-document', component: () => import('../views/DocumentView.vue'), props: true },
      { path: 'branches', name: 'ceramic-admin-branches', component: () => import('../views/BranchListView.vue') },
      { path: 'branches/:branchId', name: 'ceramic-admin-branch', component: () => import('../views/EditView.vue'), props: true },
      { path: 'tasks', name: 'ceramic-admin-tasks', component: () => import('../views/TaskListView.vue') },
      { path: 'properties', name: 'ceramic-admin-properties', component: () => import('../views/PropertiesView.vue'), meta: { minRole: 'moderator' } },
      { path: 'maintenance', name: 'ceramic-admin-maintenance', component: () => import('../views/AdminView.vue'), meta: { minRole: 'admin' } },
      { path: 'server-log', name: 'ceramic-admin-server-log', component: () => import('../views/ServerLogView.vue'), meta: { minRole: 'admin' } },
      { path: 'access-denied', name: 'ceramic-admin-access-denied', component: () => import('../views/AccessDeniedView.vue') },
    ],
  },

  // Раздел /edit расформирован: его экраны живут в /admin (см. выше).
  { path: '/edit/:pathMatch(.*)*', redirect: '/admin' },
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
  const { authChecked, user, hasRole, checkAuth } = useAuth()
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
})

export default router
