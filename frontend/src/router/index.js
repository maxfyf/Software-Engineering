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
            component: () => import('@/views/LoginView.vue')
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
            meta: { requiresAuth: true }
        }
    ]
})

// 全局前置路由守卫
router.beforeEach((to, from, next) => {
    // 检查是否需要登录
    if (to.meta.requiresAuth) {
        const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true'

        if (!isLoggedIn) {
            // 未登录，重定向到登录页
            next('/login')
        } else {
            // 已登录，继续访问
            next()
        }
    } else {
        // 不需要登录的页面，直接访问
        next()
    }
})

export default router