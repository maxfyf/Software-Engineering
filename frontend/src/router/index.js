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
            redirect: '/task/all',
            children: [
                {
                    path: 'all',
                    name: 'allTasks',
                    component: () => import('@/views/task/AllTasksView.vue')
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

export default router