import {ElMessage, ElMessageBox} from 'element-plus'
import { reactive, ref } from 'vue'
import api from '@/request/api.js'

// 用户数据结构
export const userInfo = {
    username: '',      // 用户名
    firstName: '',     // 名
    lastName: '',      // 姓
    phone: '',         // 电话号码
    email: ''          // 电子邮箱
}

// 任务数据结构
export const taskInfo = {
    id: null,
    title: '',
    description: '',
    status: '',
    priority: '',
    deadline: '',
    createdAt: '',
    updatedAt: ''
}

// 当前登录用户信息
export const currentUser = reactive({ ...userInfo })

// 登录状态
export const isLoggedIn = ref(false)

// 重置用户信息
export const resetUserInfo = () => {
    Object.keys(userInfo).forEach(key => {
        currentUser[key] = userInfo[key]
    })
}

// 当前用户的任务列表
export const taskList = ref([])

// 重置任务列表
export const resetTaskList = () => {
    taskList.value = []
}

// 高亮任务的ID
export const highlightTaskId = ref(null)

// 添加任务
export const addTask = async (task) => {
    const res = await api.createTask({
        ...task,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    })
    const newTask = res.data
    highlightTaskId.value = newTask.id
    taskList.value.push(newTask)
    return newTask
}

// 删除任务
export const removeTask = async (taskId) => {
    await api.deleteTask(taskId)
    const index = taskList.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
        taskList.value.splice(index, 1)
    }
    return true
}

// 根据ID获取任务详情
export const getTaskById = async (taskId) => {
    const res = await api.getTaskById(taskId)
    return res.data
}

// 更新任务
export const updateTask = async (taskId, taskData) => {
    await api.updateTask(taskId, {
        ...taskData,
        updatedAt: new Date().toISOString()
    })
    const index = taskList.value.findIndex(t => t.id === taskId)
    if (index !== -1) {
        taskList.value[index] = {
            ...taskList.value[index],
            ...taskData,
            updatedAt: new Date().toISOString()
        }
    }
    return true
}

// 初始化任务列表
export const initTaskList = async () => {
    try {
        const res = await api.getTaskList()
        taskList.value = res.data
    } catch (error) {
        console.error('获取任务列表失败:', error)
    }
}

// 初始化用户信息
export const initUserInfo = async () => {
    const savedIsLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true'
    const savedUsername = sessionStorage.getItem('username')

    if (savedIsLoggedIn && savedUsername) {
        isLoggedIn.value = true
        currentUser.username = savedUsername
        try {
            const res = await api.getUserInfo()
            const info = res.data
            currentUser.username = info.username
            currentUser.firstName = info.firstName
            currentUser.lastName = info.lastName
            currentUser.phone = info.phone
            currentUser.email = info.email
        } catch (error) {
            console.error('获取用户信息失败:', error)
        }
    } else {
        isLoggedIn.value = false
    }
}

/**
 * 验证密码格式
 * @param {string} password - 待验证的密码
 * @returns {boolean} - 密码是否符合要求（长度>=6 且同时包含字母和数字）
 */
export const validatePassword = (password) => {
    if (!password || password.length < 6) {
        return false
    }
    const hasLetter = /[a-zA-Z]/.test(password)
    const hasNumber = /[0-9]/.test(password)
    return hasLetter && hasNumber
}

/**
 * 验证用户名格式
 * @param {string} username - 待验证的用户名
 * @returns {boolean} - 用户名是否符合要求（字母、数字、下划线，长度 4-20）
 */
export const validateUsername = (username) => {
    if (!username || username.length < 4 || username.length > 20) {
        return false
    }
    return /^[a-zA-Z0-9_]+$/.test(username)
}

/**
 * 验证电话号码格式
 * @param {string} phoneNum - 待验证的电话号码
 * @returns {boolean} - 是否为 8 位或 11 位数字
 */
export const validatePhone = (phoneNum) => {
    if (!phoneNum) {
        return false
    }
    return /^\d{8}$|^\d{11}$/.test(phoneNum)
}

/**
 * 验证邮箱格式
 * @param {string} emailAddr - 待验证的邮箱地址
 * @returns {boolean} - 是否符合"(字符)@(字符).(字符)"格式
 */
export const validateEmail = (emailAddr) => {
    if (!emailAddr) {
        return false
    }
    return /^[^@]+@[^@]+\.[^@]+$/.test(emailAddr)
}

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
        ElMessage.error('用户名只允许包含字母、数字、下划线，长度为4～20')
        return false
    }

    if (!validatePassword(firstTimePassword)) {
        ElMessage.error('密码长度不少于6位，且必须同时包含字母和数字')
        return false
    }

    if (firstTimePassword !== repeatedPassword) {
        ElMessage.error('两次输入的密码不一致')
        return false
    }

    if (!validatePhone(phone)) {
        ElMessage.error('电话号码必须为8位或11位数字')
        return false
    }

    if (!validateEmail(email)) {
        ElMessage.error('邮箱格式不正确，应为"xxx@xxx.xxx"')
        return false
    }
    
    try {
        // 调用注册 API
        await api.register({
            username,
            password: firstTimePassword,
            first_name: firstName,
            last_name: lastName,
            phone_number: phone,
            email
        })
        
        ElMessage.success('注册成功')
        
        // 6. 将变量全部重置为空串
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
        }
    } catch (error) {
        return { success: false }
    }
}


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
            try {
                await api.cancelAccount()
            } catch (error) {
                console.error('注销账号失败:', error)
            }
            resetUserInfo()
            resetTaskList()
            sessionStorage.removeItem('isLoggedIn')
            sessionStorage.removeItem('username')
            sessionStorage.removeItem('token')
            isLoggedIn.value = false
            ElMessage.success('账号已注销')
            resolve({ success: true, redirect: '/login' })
        }).catch(() => {
            resolve({ success: false })
        })
    })
}

export const handleLogin = async ({ username, password }) => {
    try {
        // 调用后端登录 API
        const res = await api.login({ username, password })
        const { token, userInfo: info } = res.data 

        // 保存token
        if (token) {
            sessionStorage.setItem('token', token)
        }

        resetTaskList()

        // 加载用户信息
        currentUser.username = info.username
        currentUser.firstName = info.firstName  
        currentUser.lastName = info.lastName    
        currentUser.phone = info.phone  
        currentUser.email = info.email  
        
        // 保存登录状态到 sessionStorage
        sessionStorage.setItem('isLoggedIn', 'true')
        sessionStorage.setItem('username', info.username)
        
        isLoggedIn.value = true
        highlightTaskId.value = null

        await initTaskList()
        
        ElMessage.success('登录成功')
        
        // 切换页面到/task 页面
        return { success: true, redirect: '/task' }
        
    } catch (error) {
        return { success: false }
    }
}

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
            try {
                await api.logout()
            } catch (error) {
                console.error('登出失败:', error)
            }
            resetUserInfo()
            resetTaskList()
            sessionStorage.removeItem('isLoggedIn')
            sessionStorage.removeItem('username')
            sessionStorage.removeItem('token')
            isLoggedIn.value = false
            ElMessage.success('登出成功')
            resolve({ success: true, redirect: '/login' })
        }).catch(() => {
            resolve({ success: false })
        })
    })
}
