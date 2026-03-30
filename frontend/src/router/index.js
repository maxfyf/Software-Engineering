import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            redirect: '/login'
        },
        {
            path: '/login',
            name: 'login',
            component: () => import('@/views/LoginView.vue'),
            meta: { isLoginPage: true }
        },
        {
            path: '/task',
            name: 'task',
            component: () => import('@/views/TaskView.vue'),
            meta: { requiresAuth: true },
            redirect: '/task/all',
            children: [
                {
                    path: 'all',
                    name: 'allTasks',
                    component: () => import('@/views/task/AllTasksView.vue')
                },
                {
                    path: 'edit',
                    name: 'editTask',
                    component: () => import('@/views/task/EditTaskView.vue')
                }
            ]
        },
        {
            path: '/settings',
            name: 'settings',
            component: () => import('@/views/SettingsView.vue'),
            meta: { requiresAuth: true },
            redirect: '/settings/info',
            children: [
                {
                    path: 'info',
                    name: 'userInfo',
                    component: () => import('@/views/settings/UserInfoView.vue'),
                }
            ]
        }
    ]
})

// 全局前置路由守卫
router.beforeEach((to, from, next) => {
    const isLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true'
    
    // 已登录且要访问登录页，阻止导航
    if (isLoggedIn && to.meta.isLoginPage) {
        next(false)
        return
    }
    
    // 如果未登录且要访问需要登录的页面
    if (to.meta.requiresAuth && !isLoggedIn) {
        next('/login')
        return
    }
    
    // 其他情况正常放行
    next()
})

export default router
