const API_CONFIG = {
    baseUrl: "/api"
};

// 1. 用户注册
export async function register(username, password) {
    return await fetch(`${API_CONFIG.baseUrl}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
}

// 2. 用户登录
export async function login(username, password) {
    return await fetch(`${API_CONFIG.baseUrl}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
}

// 3. 创建任务
export async function createTask(taskData, token) {
    return await fetch(`${API_CONFIG.baseUrl}/tasks`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(taskData)
    });
}

// 4. 获取任务列表
export async function getTaskList(token) {
    return await fetch(`${API_CONFIG.baseUrl}/tasks`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${token}` }
    });
}

// 5. 获取任务详情
export async function getTaskDetail(taskId, token) {
    return await fetch(`${API_CONFIG.baseUrl}/tasks/${taskId}`, {
        method: "GET",
        headers: { "Authorization": `Bearer ${token}` }
    });
}

// 6. 修改任务
export async function updateTask(taskId, taskData, token) {
    return await fetch(`${API_CONFIG.baseUrl}/tasks/${taskId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(taskData)
    });
}

// 7. 删除任务
export async function deleteTask(taskId, token) {
    return await fetch(`${API_CONFIG.baseUrl}/tasks/${taskId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
    });
}