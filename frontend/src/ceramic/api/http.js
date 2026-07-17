import axios from 'axios'

const MUTATING_METHODS = new Set(['post', 'put', 'patch', 'delete'])

function readCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'))
  return match ? decodeURIComponent(match[1]) : null
}

const http = axios.create({
  withCredentials: true,
})

http.interceptors.request.use((config) => {
  const method = (config.method || 'get').toLowerCase()
  if (MUTATING_METHODS.has(method)) {
    const csrfToken = readCookie('csrf_token')
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken
    }
  }
  return config
})

export default http
