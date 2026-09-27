import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    redirect: '/patients',
  },
  {
    path: '/patients',
    name: 'PatientList',
    component: () => import('../views/PatientListView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/patients/:id',
    name: 'PatientDetail',
    component: () => import('../views/PatientDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/patients/:id/upload',
    name: 'ImageUpload',
    component: () => import('../views/ImageUploadView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/results/:id',
    name: 'DetectionResult',
    component: () => import('../views/DetectionResultView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/HistoryView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/audit',
    name: 'Audit',
    component: () => import('../views/AuditLogView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { top: 0, left: 0 }
  },
})

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('access_token')
  const auth = useAuthStore()

  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/patients')
  } else if (to.meta.requiresAdmin) {
    // 确保用户信息已加载，再判断管理员权限
    if (!auth.user) {
      try {
        await auth.fetchUser()
      } catch {
        // 忽略，下面会兜底
      }
    }
    if (auth.user?.role !== 'admin') {
      ElMessage.warning('无权限访问该页面')
      next('/patients')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
