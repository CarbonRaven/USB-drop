import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for token refresh
api.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh', {
            refresh_token: refreshToken
          })

          const newToken = response.data.access_token
          localStorage.setItem('accessToken', newToken)
          localStorage.setItem('refreshToken', response.data.refresh_token)

          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return api(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('accessToken')
          localStorage.removeItem('refreshToken')
          window.location.href = '/login'
        }
      }
    }

    return Promise.reject(error)
  }
)

export default api

// API helper functions
export const campaignsApi = {
  list: () => api.get('/campaigns'),
  get: (id) => api.get(`/campaigns/${id}`),
  create: (data) => api.post('/campaigns', data),
  update: (id, data) => api.put(`/campaigns/${id}`, data),
  delete: (id) => api.delete(`/campaigns/${id}`),
  stats: (id) => api.get(`/campaigns/${id}/stats`),
}

export const drivesApi = {
  list: (params) => api.get('/drives', { params }),
  get: (id) => api.get(`/drives/${id}`),
  getByCode: (code) => api.get(`/drives/by-code/${code}`),
  create: (data) => api.post('/drives', data),
  update: (id, data) => api.put(`/drives/${id}`, data),
  prepare: (id) => api.post(`/drives/${id}/prepare`),
  deploy: (id, data) => api.post(`/drives/${id}/deploy`, data),
  download: (id) => api.get(`/drives/${id}/download`, { responseType: 'blob' }),
  tokens: (id) => api.get(`/drives/${id}/tokens`),
}

export const profilesApi = {
  list: () => api.get('/profiles'),
  get: (id) => api.get(`/profiles/${id}`),
  create: (data) => api.post('/profiles', data),
  update: (id, data) => api.put(`/profiles/${id}`, data),
  delete: (id) => api.delete(`/profiles/${id}`),
  preview: (id) => api.get(`/profiles/${id}/preview`),
}

export const alertsApi = {
  list: (params) => api.get('/alerts', { params }),
  recent: (hours = 24) => api.get('/alerts/recent', { params: { hours } }),
  stats: (campaignId) => api.get('/alerts/stats', { params: { campaign_id: campaignId } }),
  map: (params) => api.get('/alerts/map', { params }),
}

export const reportsApi = {
  campaign: (id) => api.get(`/reports/campaign/${id}`),
  exportCsv: (id) => api.get(`/reports/export/${id}/csv`, { responseType: 'blob' }),
  summary: () => api.get('/reports/summary'),
}
