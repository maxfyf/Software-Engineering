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
        const status = error.response?.status
        const detail = error.response?.data?.detail
        const msg = error.response?.data?.msg
        const isLoginRequest = error.config.url.includes('/user/login')
        
        if (status === 401) {
            if (isLoginRequest) {
                // 登录接口的401错误，直接显示错误信息
                ElMessage.error(detail || '密码错误')
            } else {
                // 其他接口的401错误，跳转登录页
                ElMessage.error('登录状态已过期，请重新登录')
                sessionStorage.clear()
                window.location.href = '/login'
            }
        } else if (status === 404) {
            if (isLoginRequest) {
                // 登录接口的404错误，显示用户不存在
                ElMessage.error(detail || '用户不存在')
            } else {
                ElMessage.error(detail || msg || '资源不存在')
            }
        } else if (status === 400 || status === 422) {
            // 显示后端返回的错误信息
            ElMessage.error(detail || msg || '请求参数错误')
        } else if (detail || msg) {
            ElMessage.error(detail || msg)
        } else {
            ElMessage.error('网络错误，请稍后重试')
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
    deleteTask: (taskId) => request.delete(`/task/${taskId}`),

    // 团队模块
    getTeamList: () => request.get('/team/list'),
    createTeam: (data) => request.post('/team/create', data),
    deleteTeam: (teamId) => request.delete(`/team/${teamId}`),
    addMember: (teamId, username, role) => request.post(`/team/${teamId}/member`, { username, role }),
    removeMember: (teamId, username) => request.delete(`/team/${teamId}/member`, { username }),
    setMemberRole: (teamId, username, role) => request.put(`/team/${teamId}/member/role`, { username, role }),
    getTeamTasks: (teamId) => request.get(`/team/${teamId}/tasks`),
    createTeamTask: (teamId, data) => request.post(`/team/${teamId}/task`, data),
    assignTask: (taskId, username) => request.put(`/task/${taskId}/assign`, { username })
}

export default api