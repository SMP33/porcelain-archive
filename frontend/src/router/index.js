import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
  { path: '/', name: 'document-list', component: () => import('../views/DocumentListView.vue') },
  { path: '/branches', name: 'branch-list', component: () => import('../views/BranchListView.vue'), meta: { requiresAuth: true } },
  { path: '/tasks', name: 'task-list', component: () => import('../views/TaskListView.vue'), meta: { requiresAuth: true } },
  { path: '/users', name: 'user-list', component: () => import('../views/UserListView.vue'), meta: { requiresAuth: true } },
  { path: '/document/:documentId', name: 'document', component: () => import('../views/DocumentView.vue'), props: true },
  { path: '/edit/:branchId', name: 'edit', component: () => import('../views/EditView.vue'), props: true },
  { path: '/access-denied', name: 'access-denied', component: () => import('../views/AccessDeniedView.vue') },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('../views/NotFoundView.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
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
