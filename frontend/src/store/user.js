import { ElMessage } from 'element-plus'
import router from '@/router'
import { reactive, ref } from 'vue'

// 用户数据结构
export const userInfo = {
    username: '',      // 用户名
    firstName: '',     // 名
    lastName: '',      // 姓
    phone: '',         // 电话号码
    email: ''          // 电子邮箱
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
 * @returns {boolean} - 是否符合"(字符)@(字符).com"格式
 */
export const validateEmail = (emailAddr) => {
    if (!emailAddr) {
        return false
    }
    return /^[^@]+@[^@]+\.com$/.test(emailAddr)
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
    /*TODO: 注册
     * 1. 在前端检查密码是否符合要求，以及两次输入密码的字符串是否相同，若不满足要求，反馈相应判定结果
     * 2. 在前端检查电话号码是否为 8 位或 11 位数字，若不满足要求，反馈相应结果
     * 3. 在前端检查邮箱字符串是否符合"(Σ*)@(Σ*).com"的格式，若不满足要求，反馈相应结果
     * 4. 在后端查找该用户名是否已经被注册过，若已经注册过，反馈相应结果
     * 5. 将新建的用户信息加入到后端数据库，提示"注册成功"，并返回登录界面，将除了 username 以外的变量全部重置为空串
     */
    
    // 1. 验证用户名格式
    if (!validateUsername(username)) {
        ElMessage.error('用户名只允许包含字母、数字、下划线，长度为 4～20')
        return false
    }
    
    // 2. 验证密码格式
    if (!validatePassword(firstTimePassword)) {
        ElMessage.error('密码长度不少于 6 位，且必须同时包含字母和数字')
        return false
    }
    
    // 3. 验证两次输入的密码是否一致
    if (firstTimePassword !== repeatedPassword) {
        ElMessage.error('两次输入的密码不一致')
        return false
    }
    
    // 4. 验证电话号码格式
    if (!validatePhone(phone)) {
        ElMessage.error('电话号码必须为 8 位或 11 位数字')
        return false
    }
    
    // 5. 验证邮箱格式
    if (!validateEmail(email)) {
        ElMessage.error('邮箱格式不正确，应为 "xxx@xxx.com"')
        return false
    }
    
    try {
        // TODO: 调用后端注册 API
        // const response = await axios.post('/api/register', { ... })
        
        // 模拟注册成功（后续替换为真实 API 调用）
        console.log('注册信息:', {
            username,
            firstName,
            lastName,
            phone,
            email
        })
        
        ElMessage.success('注册成功！请登录')
        
        // 切换到登录界面
        router.push('/login')
        return true
        
    } catch (error) {
        console.error('注册失败:', error)
        ElMessage.error('注册失败，请稍后重试')
        return false
    }
}

export const handleLogin = async ({ username, password }) => {
    /*TODO: 登录
     * 1. 在后端数据库中查询该用户，并反馈"用户不存在"、"密码错误"或"登录成功"三种结果
     * 2. 从后端加载用户信息与所有任务，存储到该文件
     * 3. 将 App.vue 中的 isLoggedIn 置为 true
     * 4. 切换页面到/task 页面
     * */
    
    try {
        // TODO: 调用后端登录 API
        // const response = await axios.post('/api/login', { username, password })
        
        // 模拟登录成功（后续替换为真实 API 调用）
        console.log('登录信息:', { username })
        
        // 2. 从后端加载用户信息（目前使用模拟数据）
        currentUser.username = username
        currentUser.firstName = 'John'  // TODO: 从后端获取
        currentUser.lastName = 'Doe'    // TODO: 从后端获取
        currentUser.phone = '12345678'  // TODO: 从后端获取
        currentUser.email = 'john@example.com'  // TODO: 从后端获取
        
        // 保存登录状态到 localStorage
        localStorage.setItem('isLoggedIn', 'true')
        localStorage.setItem('username', username)
        
        // 3. 将 isLoggedIn 置为 true
        isLoggedIn.value = true
        
        ElMessage.success('登录成功')
        
        // 4. 切换页面到/task 页面
        router.push('/task')
        return true
        
    } catch (error) {
        console.error('登录失败:', error)
        // TODO: 根据后端返回的错误信息显示不同提示
        ElMessage.error('用户名或密码错误')
        return false
    }
}

export const handleLogout = () => {
    /*TODO: 登出
     * 1. 删去用户数据
     * 2. 将 App.vue 中的 isLoggedIn 置为 false
     * 3. 切换页面到 login 页面
     * */
    
    // 1. 删除用户数据
    resetUserInfo()
    
    // 清除 localStorage 中的登录状态
    localStorage.removeItem('isLoggedIn')
    localStorage.removeItem('username')
    
    // 2. 更新登录状态为 false
    isLoggedIn.value = false
    
    ElMessage.success('已退出登录')
    
    // 3. 切换页面到 login 页面
    router.push('/login')
}
