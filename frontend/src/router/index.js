import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'

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
  // Porcelain (архив документов) - отдельная ветка /edit, чтобы не пересекаться
  // с публичным ceramic-сайтом на корневом домене (свои роуты, свой useAuth).
  { path: '/edit/all-pages', name: 'all-pages', component: () => import('../views/AllPagesView.vue') },
  { path: '/edit/login', name: 'login', component: () => import('../views/LoginView.vue') },
  { path: '/edit', name: 'document-list', component: () => import('../views/DocumentListView.vue') },
  { path: '/edit/branches', name: 'branch-list', component: () => import('../views/BranchListView.vue'), meta: { requiresAuth: true } },
  { path: '/edit/tasks', name: 'task-list', component: () => import('../views/TaskListView.vue'), meta: { requiresAuth: true } },
  { path: '/edit/users', name: 'user-list', component: () => import('../views/UserListView.vue'), meta: { requiresAuth: true } },
  { path: '/edit/server-log', name: 'server-log', component: () => import('../views/ServerLogView.vue'), meta: { requiresAuth: true } },
  { path: '/edit/admin', name: 'admin', component: () => import('../views/AdminView.vue'), meta: { requiresAuth: true } },
  { path: '/edit/properties', name: 'properties', component: () => import('../views/PropertiesView.vue'), meta: { requiresAuth: true } },
  { path: '/edit/feedback', name: 'feedback-list', component: () => import('../views/FeedbackView.vue'), meta: { requiresAuth: true } },
  { path: '/edit/subscribers', name: 'subscriber-list', component: () => import('../views/SubscribersView.vue'), meta: { requiresAuth: true } },
  { path: '/edit/document/:documentId', name: 'document', component: () => import('../views/DocumentView.vue'), props: true },
  { path: '/edit/:branchId', name: 'edit', component: () => import('../views/EditView.vue'), props: true },
  { path: '/edit/access-denied', name: 'access-denied', component: () => import('../views/AccessDeniedView.vue') },
  { path: '/edit/:pathMatch(.*)*', name: 'not-found', component: () => import('../views/NotFoundView.vue') },
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
  // Ветка Porcelain (/edit) - своя авторизация, не связана с useAuth ceramic.
  if (to.path.startsWith('/edit')) {
    const { authChecked, user, checkAuth } = useAuth()
    if (!authChecked.value) {
      await checkAuth()
    }
    if (to.meta.requiresAuth && !user.value) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    return true
  }

  return true
})

export default router
