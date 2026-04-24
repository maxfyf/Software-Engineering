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
                    component: () => import('@/views/task/AllTasksView.vue'),
                    children: [
                        {
                            path: 'edit',
                            name: 'allTasksEdit',
                            component: () => import('@/views/task/EditTaskView.vue')
                        }
                    ]
                },
                {
                    path: 'personal',
                    name: 'personalTasks',
                    component: () => import('@/views/task/PersonalTasksView.vue'),
                    children: [
                        {
                            path: 'edit',
                            name: 'personalTasksEdit',
                            component: () => import('@/views/task/EditTaskView.vue')
                        }
                    ]
                },
                {
                    path: 'team',
                    name: 'teamTasks',
                    component: () => import('@/views/task/TeamTasksView.vue'),
                    children: [
                        {
                            path: 'edit',
                            name: 'teamTasksEdit',
                            component: () => import('@/views/task/EditTaskView.vue')
                        }
                    ]
                }
            ]
        },
        {
            path: '/team',
            name: 'team',
            component: () => import('@/views/TeamView.vue'),
            meta: { requiresAuth: true },
            redirect: '/team/all',
            children: [
                {
                    path: 'all',
                    name: 'allTeams',
                    component: () => import('@/views/team/AllTeamsView.vue'),
                    children: [
                        {
                            path: 'space',
                            name: 'allTeamsSpace',
                            component: () => import('@/views/team/TeamSpaceView.vue'),
                            children: [
                                {
                                    path: 'personnel',
                                    name: 'allTeamsPersonnel',
                                    component: () => import('@/views/team/PersonnelView.vue')
                                },
                                {
                                    path: 'edit',
                                    name: 'allTeamsEdit',
                                    component: () => import('@/views/task/EditTaskView.vue')
                                }
                            ]
                        }
                    ]
                },
                {
                    path: 'owner',
                    name: 'ownerTeams',
                    component: () => import('@/views/team/OwnerTeamsView.vue'),
                    children: [
                        {
                            path: 'space',
                            name: 'ownerTeamsSpace',
                            component: () => import('@/views/team/TeamSpaceView.vue'),
                            children: [
                                {
                                    path: 'personnel',
                                    name: 'ownerTeamsPersonnel',
                                    component: () => import('@/views/team/PersonnelView.vue')
                                },
                                {
                                    path: 'edit',
                                    name: 'ownerTeamsEdit',
                                    component: () => import('@/views/task/EditTaskView.vue')
                                }
                            ]
                        }
                    ]
                },
                {
                    path: 'admin',
                    name: 'adminTeams',
                    component: () => import('@/views/team/AdminTeamsView.vue'),
                    children: [
                        {
                            path: 'space',
                            name: 'adminTeamsSpace',
                            component: () => import('@/views/team/TeamSpaceView.vue'),
                            children: [
                                {
                                    path: 'personnel',
                                    name: 'adminTeamsPersonnel',
                                    component: () => import('@/views/team/PersonnelView.vue')
                                },
                                {
                                    path: 'edit',
                                    name: 'adminTeamsEdit',
                                    component: () => import('@/views/task/EditTaskView.vue')
                                }
                            ]
                        }
                    ]
                },
                {
                    path: 'member',
                    name: 'memberTeams',
                    component: () => import('@/views/team/MemberTeamsView.vue'),
                    children: [
                        {
                            path: 'space',
                            name: 'memberTeamsSpace',
                            component: () => import('@/views/team/TeamSpaceView.vue'),
                            children: [
                                {
                                    path: 'personnel',
                                    name: 'memberTeamsPersonnel',
                                    component: () => import('@/views/team/PersonnelView.vue')
                                },
                                {
                                    path: 'edit',
                                    name: 'memberTeamsEdit',
                                    component: () => import('@/views/task/EditTaskView.vue')
                                }
                            ]
                        }
                    ]
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
