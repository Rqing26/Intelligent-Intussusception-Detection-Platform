import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getCurrentUser } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const user = ref(null)

  async function login(username, password) {
    const res = await loginApi(username, password)
    token.value = res.data.access_token
    localStorage.setItem('access_token', token.value)
    await fetchUser()
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const res = await getCurrentUser()
      user.value = res.data
    } catch {
      logout()
    }
  }

  return { token, user, login, logout, fetchUser }
})
