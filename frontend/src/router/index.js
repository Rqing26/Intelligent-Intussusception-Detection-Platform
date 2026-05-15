import { createRouter, createWebHashHistory } from 'vue-router'

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
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/patients')
  } else {
    next()
  }
})

export default router
