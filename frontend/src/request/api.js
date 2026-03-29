import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { reactive, ref } from 'vue';

// ===================== 1. Axios 基础配置 =====================
const service = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json;charset=utf-8'
    }
});

// 请求拦截器
service.interceptors.request.use(
    (config) => {
        const token = sessionStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// 响应拦截器
service.interceptors.response.use(
    (response) => {
        const res = response.data;
        if (!res.success) {
            ElMessage.error(res.msg || '请求失败');
            return Promise.reject(res);
        }
        return res;
    },
    (error) => {
        if (error.response?.status === 401) {
            ElMessage.error('登录状态已过期，请重新登录');
            sessionStorage.clear();
            isLoggedIn.value = false;
            window.location.href = '/login';
        } else {
            ElMessage.error(error.response?.data?.msg || '服务器错误');
        }
        return Promise.reject(error);
    }
);

const request = {
    get: (url, params = {}) => service.get(url, { params }),
    post: (url, data = {}) => service.post(url, data),
    put: (url, data = {}) => service.put(url, data),
    delete: (url, params = {}) => service.delete(url, { params })
};

// ===================== 2. 数据结构定义 =====================
export const userInfo = {
    username: '',
    firstName: '',
    lastName: '',
    phone: '',
    email: ''
};

export const taskInfo = {
    id: null,
    title: '',
    description: '',
    status: '',
    priority: '',
    deadline: '',
    createdAt: '',
    updatedAt: ''
};

// ===================== 3. 全局状态 =====================
export const currentUser = reactive({ ...userInfo });
export const isLoggedIn = ref(false);
export const taskList = ref([]);

// ===================== 4. 工具函数 =====================
export const resetUserInfo = () => {
    Object.keys(userInfo).forEach(key => {
        currentUser[key] = userInfo[key];
    });
};

export const resetTaskList = () => {
    taskList.value = [];
};

export const validatePassword = (password) => {
    if (!password || password.length < 6) return false;
    return /[a-zA-Z]/.test(password) && /[0-9]/.test(password);
};

export const validateUsername = (username) => {
    if (!username || username.length < 4 || username.length > 20) return false;
    return /^[a-zA-Z0-9_]+$/.test(username);
};

export const validatePhone = (phoneNum) => {
    if (!phoneNum) return false;
    return /^\d{8}$|^\d{11}$/.test(phoneNum);
};

export const validateEmail = (emailAddr) => {
    if (!emailAddr) return false;
    return /^[^@]+@[^@]+\.[^@]+$/.test(emailAddr);
};

// ===================== 5. API 接口封装 =====================
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
};

// ===================== 6. 业务逻辑实现 =====================

// 添加任务
export const addTask = async (task) => {
    try {
        const res = await api.createTask({
            ...taskInfo,
            ...task,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        });
        const newTask = res.data;
        taskList.value.push(newTask);
        ElMessage.success('任务创建成功');
        return newTask;
    } catch (error) {
        ElMessage.error('任务创建失败');
        return null;
    }
};

// 删除任务
export const removeTask = async (taskId) => {
    try {
        await api.deleteTask(taskId);
        const index = taskList.value.findIndex(t => t.id === taskId);
        if (index !== -1) {
            taskList.value.splice(index, 1);
        }
        return true;
    } catch (error) {
        ElMessage.error('任务删除失败');
        return false;
    }
};

// 根据ID获取任务详情
export const getTaskById = async (taskId) => {
    try {
        const res = await api.getTaskById(taskId);
        return res.data;
    } catch (error) {
        ElMessage.error('获取任务详情失败');
        return null;
    }
};

// 注册处理
export const handleRegister = async ({
                                         username,
                                         firstTimePassword,
                                         repeatedPassword,
                                         firstName,
                                         lastName,
                                         phone,
                                         email
                                     }) => {
    if (!validateUsername(username)) {
        ElMessage.error('用户名只允许包含字母、数字、下划线，长度为4～20');
        return false;
    }
    if (!validatePassword(firstTimePassword)) {
        ElMessage.error('密码长度不少于6位，且必须同时包含字母和数字');
        return false;
    }
    if (firstTimePassword !== repeatedPassword) {
        ElMessage.error('两次输入的密码不一致');
        return false;
    }
    if (!validatePhone(phone)) {
        ElMessage.error('电话号码必须为8位或11位数字');
        return false;
    }
    if (!validateEmail(email)) {
        ElMessage.error('邮箱格式不正确，应为"xxx@xxx.xxx"');
        return false;
    }

    try {
        await api.register({
            username,
            password: firstTimePassword,
            firstName,
            lastName,
            phone,
            email
        });
        ElMessage.success('注册成功');
        return {
            success: true,
            resetFields: {
                username: '',
                firstTimePassword: '',
                repeatedPassword: '',
                firstName: '',
                lastName: '',
                phone: '',
                email: ''
            }
        };
    } catch (error) {
        console.error('注册失败:', error);
        ElMessage.error('注册失败');
        return { success: false };
    }
};

// 注销账号
export const handleCancelAccount = () => {
    return new Promise((resolve) => {
        ElMessageBox.confirm(
            '注销账号后，您的所有数据将被删除且无法恢复，确定要注销吗？',
            '',
            {
                confirmButtonText: '确定注销',
                confirmButtonType: 'danger',
                cancelButtonText: '取消',
                type: undefined
            }
        ).then(async () => {
            await api.cancelAccount();
            resetUserInfo();
            resetTaskList();
            sessionStorage.removeItem('isLoggedIn');
            sessionStorage.removeItem('username');
            sessionStorage.removeItem('token');
            isLoggedIn.value = false;
            ElMessage.success('账号已注销');
            resolve({ success: true, redirect: '/login' });
        }).catch(() => {
            resolve({ success: false });
        });
    });
};

// 登录处理
export const handleLogin = async ({ username, password }) => {
    try {
        const res = await api.login({ username, password });
        const { token, userInfo } = res.data;

        sessionStorage.setItem('token', token);
        currentUser.username = userInfo.username;
        currentUser.firstName = userInfo.firstName;
        currentUser.lastName = userInfo.lastName;
        currentUser.phone = userInfo.phone;
        currentUser.email = userInfo.email;
        sessionStorage.setItem('isLoggedIn', 'true');
        sessionStorage.setItem('username', username);
        isLoggedIn.value = true;

        ElMessage.success('登录成功');
        return { success: true, redirect: '/task' };
    } catch (error) {
        console.error('登录失败:', error);
        ElMessage.error('用户名或密码错误');
        return false;
    }
};

// 登出处理
export const handleLogout = () => {
    return new Promise((resolve) => {
        ElMessageBox.confirm(
            '确认退出登录？',
            '',
            {
                confirmButtonText: '确定',
                confirmButtonType: 'danger',
                cancelButtonText: '取消',
                type: undefined
            }
        ).then(async () => {
            await api.logout();
            resetUserInfo();
            sessionStorage.removeItem('isLoggedIn');
            sessionStorage.removeItem('username');
            sessionStorage.removeItem('token');
            isLoggedIn.value = false;
            ElMessage.success('登出成功');
            resolve({ success: true, redirect: '/login' });
        }).catch(() => {
            resolve({ success: false });
        });
    });
};

// 初始化任务列表
export const initTaskList = async () => {
    try {
        const res = await api.getTaskList();
        taskList.value = res.data;
    } catch (error) {
        console.error('获取任务列表失败:', error);
        ElMessage.error('加载任务列表失败');
        // 模拟数据兜底
        taskList.value = [
            {
                id: 1,
                title: "完成前端登录界面",
                description: "实现用户登录、注册的前端界面",
                status: "进行中",
                priority: "高",
                deadline: "2026-04-01",
                createdAt: "2026-03-20",
                updatedAt: "2026-03-20"
            },
            {
                id: 2,
                title: "完成后端API接口",
                description: "实现用户注册、登录的后端接口",
                status: "进行中",
                priority: "中",
                deadline: "2026-04-05",
                createdAt: "2026-03-20",
                updatedAt: "2026-03-20"
            }
        ];
    }
};

// 初始化用户信息（页面刷新后调用）
export const initUserInfo = async () => {
    const savedIsLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true';
    const savedUsername = sessionStorage.getItem('username');

    if (savedIsLoggedIn && savedUsername) {
        isLoggedIn.value = true;
        try {
            const res = await api.getUserInfo();
            const userInfo = res.data;
            currentUser.username = userInfo.username;
            currentUser.firstName = userInfo.firstName;
            currentUser.lastName = userInfo.lastName;
            currentUser.phone = userInfo.phone;
            currentUser.email = userInfo.email;
        } catch (error) {
            console.error('获取用户信息失败:', error);
            sessionStorage.clear();
            isLoggedIn.value = false;
            ElMessage.error('登录状态失效，请重新登录');
            window.location.href = '/login';
        }
    } else {
        isLoggedIn.value = false;
    }
};

// 更新任务
export const updateTask = async (taskId, taskData) => {
    try {
        await api.updateTask(taskId, {
            ...taskData,
            updatedAt: new Date().toISOString()
        });
        const index = taskList.value.findIndex(t => t.id === taskId);
        if (index !== -1) {
            taskList.value[index] = {
                ...taskList.value[index],
                ...taskData,
                updatedAt: new Date().toISOString()
            };
        }
        ElMessage.success('任务更新成功');
        return true;
    } catch (error) {
        ElMessage.error('任务更新失败');
        return false;
    }
};

export default {
    currentUser,
    isLoggedIn,
    taskList,
    addTask,
    removeTask,
    getTaskById,
    handleRegister,
    handleCancelAccount,
    handleLogin,
    handleLogout,
    initTaskList,
    initUserInfo,
    updateTask,
    validatePassword,
    validateUsername,
    validatePhone,
    validateEmail
};