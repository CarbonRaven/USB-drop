import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/campaigns',
    name: 'Campaigns',
    component: () => import('@/views/Campaigns.vue')
  },
  {
    path: '/campaigns/:id',
    name: 'CampaignDetail',
    component: () => import('@/views/CampaignDetail.vue')
  },
  {
    path: '/profiles',
    name: 'Profiles',
    component: () => import('@/views/Profiles.vue')
  },
  {
    path: '/drives',
    name: 'Drives',
    component: () => import('@/views/Drives.vue')
  },
  {
    path: '/drives/:id',
    name: 'DriveDetail',
    component: () => import('@/views/DriveDetail.vue')
  },
  {
    path: '/map',
    name: 'Map',
    component: () => import('@/views/MapView.vue')
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/Alerts.vue')
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/Reports.vue')
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (!to.meta.public && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
