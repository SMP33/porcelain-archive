import { ref } from 'vue'
import http from '../api/http'

const user = ref(null)
const authChecked = ref(false)

const showResetPasswordDialog = ref(false)
const oldPassword = ref('')
const newPassword = ref('')
const resetPasswordLoading = ref(false)
const resetPasswordError = ref('')

const showSetDisplayNameDialog = ref(false)
const displayNameInput = ref('')
const setDisplayNameLoading = ref(false)
const setDisplayNameError = ref('')

async function checkAuth() {
  try {
    const response = await http.get('/api/users/me')
    user.value = response.data
  } catch (error) {
    user.value = null
  } finally {
    authChecked.value = true
  }
}

async function handleLogout() {
  try {
    await http.post('/api/users/logout', {})
    user.value = null
  } catch (error) {
    console.error('Ошибка при выходе:', error)
  }
}

async function handleResetPassword() {
  resetPasswordLoading.value = true
  resetPasswordError.value = ''
  try {
    await http.post('/api/users/reset_password', {
      old_password: oldPassword.value,
      new_password: newPassword.value,
    })
    showResetPasswordDialog.value = false
    oldPassword.value = ''
    newPassword.value = ''
  } catch (error) {
    resetPasswordError.value = 'Не удалось сменить пароль.'
    console.error('Ошибка при смене пароля:', error)
  } finally {
    resetPasswordLoading.value = false
  }
}

async function handleSetDisplayName() {
  setDisplayNameLoading.value = true
  setDisplayNameError.value = ''
  try {
    const response = await http.post('/api/users/set_display_name', {
      display_name: displayNameInput.value,
    })
    if (user.value) {
      user.value.display_name = response.data.display_name
    }
    showSetDisplayNameDialog.value = false
  } catch (error) {
    setDisplayNameError.value = 'Не удалось изменить ФИО.'
    console.error('Ошибка при изменении ФИО:', error)
  } finally {
    setDisplayNameLoading.value = false
  }
}

export function useAuth() {
  return {
    user,
    authChecked,
    checkAuth,
    handleLogout,
    showResetPasswordDialog,
    oldPassword,
    newPassword,
    resetPasswordLoading,
    resetPasswordError,
    handleResetPassword,
    showSetDisplayNameDialog,
    displayNameInput,
    setDisplayNameLoading,
    setDisplayNameError,
    handleSetDisplayName,
  }
}
