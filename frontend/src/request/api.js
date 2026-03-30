import axios from 'axios'
import { ElMessage } from 'element-plus'

// Axios 基础配置
const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json;charset=utf-8'
    }
})

// 请求拦截器
service.interceptors.request.use(
    (config) => {
        const token = sessionStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// 响应拦截器
service.interceptors.response.use(
    (response) => {
        const res = response.data
        if (!res.success) {
            ElMessage.error(res.msg || '请求失败')
            return Promise.reject(res)
        }
        return res
    },
    (error) => {
        if (error.response?.status === 401) {
            ElMessage.error('登录状态已过期，请重新登录')
            sessionStorage.clear()
            window.location.href = '/login'
        } else if (error.response){
            ElMessage.error(error.response?.data?.msg || '请求失败')
        }
        return Promise.reject(error)
    }
)

const request = {
    get: (url, params = {}) => service.get(url, { params }),
    post: (url, data = {}) => service.post(url, data),
    put: (url, data = {}) => service.put(url, data),
    delete: (url, params = {}) => service.delete(url, { params })
}

// API 接口封装
const api = {
    // 用户模块
    register: (data) => request.post('/user/register', data),
    login: (data) => request.post('/user/login', data),
    logout: () => request.post('/user/logout'),
    getUserInfo: () => request.get('/user/info'),
    cancelAccount: () => request.delete('/user/cancel'),

    // 任务模块
    getTaskList: () => request.get('/task/list'),
    getTaskById: (taskId) => request.get(`/task/${taskId}`),
    createTask: (data) => request.post('/task/create', data),
    updateTask: (taskId, data) => request.put(`/task/${taskId}`, data),
    deleteTask: (taskId) => request.delete(`/task/${taskId}`)
}

export default api