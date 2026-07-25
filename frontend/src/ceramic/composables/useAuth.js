import { ref } from 'vue'
import http from '../api/http'

// Иерархия ролей общая с архивом (см. ROLES.md); contributor - синоним user
const ROLE_LEVELS = { user: 1, contributor: 1, moderator: 2, admin: 3 }

const user = ref(null)
const authChecked = ref(false)

function hasRole(minRole) {
  if (!user.value) {
    return false
  }
  return (ROLE_LEVELS[user.value.role] || 0) >= ROLE_LEVELS[minRole]
}

async function checkAuth() {
  try {
    const response = await http.get('/api/ceramic/users/me')
    user.value = response.data
  } catch (error) {
    user.value = null
  } finally {
    authChecked.value = true
  }
}

async function login(username, password) {
  const response = await http.post('/api/ceramic/users/login', { username, password })
  user.value = response.data
  authChecked.value = true
  return response.data
}

async function logout() {
  try {
    await http.post('/api/ceramic/users/logout')
  } finally {
    user.value = null
  }
}

export function useAuth() {
  return {
    user,
    authChecked,
    hasRole,
    checkAuth,
    login,
    logout,
  }
}
