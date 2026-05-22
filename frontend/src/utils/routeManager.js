import { currentUser } from '@/store/user.js'
import { taskList, teamList } from "@/store/user.js";

// 路由解析器
const routeParser = (route) => {
    let path = route.fullPath.split('/')
    if(path.length === 0) return undefined

    let lastIndex = path[path.length - 1].split('?')
    if(lastIndex.length === 1)
    {
        return {
            path: path,
            params: []
        }
    }
    else
    {
        path[path.length - 1] = lastIndex[0]
        let paramList = lastIndex[1].split('&')
        let params = []
        for(let paramStr of paramList) {
            let param = paramStr.split('=')
            let key = param[0]
            let value = param[1]
            params.push({
                key: key,
                value: value
            })
        }
        return {
            path: path,
            params: params
        }
    }
}

// 进入页面
export const handleEnter = (route, router, newPage) => {
    const res = routeParser(route)
    if(!res) return false

    res.path.push(newPage.path)
    const newRoute = res.path.join('/')

    let params = res.params
    if(newPage.params.length > 0)
        params.push(...newPage.params)
    const queryObj = {}
    params.forEach((param) => {
        queryObj[param.key] = param.value
    })

    router.push({
        path: newRoute,
        query: queryObj
    })
    return true
}

// 退出页面
export const handleBack = (route, router, num) => {
    if(num <= 0) return false
    const res = routeParser(route)
    if(!res || res.path.length <= num) return false

    res.path.length -= num
    const newRoute = res.path.join('/')

    let keys = new Set()
    if(newRoute.indexOf('detail') !== -1) keys.add('taskId')
    if(newRoute.indexOf('edit') !== -1) keys.add('isNew').add('taskId')
    if(newRoute.indexOf('space') !== -1) keys.add('teamId')

    const params = res.params.filter(param => keys.has(param.key));
    const queryObj = {}
    params.forEach((param) => {
        queryObj[param.key] = param.value
    })
    router.push({
        path: newRoute,
        query: queryObj
    })
    return true
}

const getParam = (params, key) => {
    const param = params.find(param => param.key === key)
    if(!param) return undefined
    else return param.value
}

// 由route路径翻译为内部路由
export const translate = (route) => {
    const res = routeParser(route)
    if(!res || res.path.length <= 1) return ''

    let innerRoute = []
    switch(res.path[1]) {
        case 'login':
            return ''
        case 'task':
            if(res.path.length <= 2) return ''
            switch(res.path[2]) {
                case 'all':
                    innerRoute.push('全部任务')
                    break
                case 'personal':
                    innerRoute.push('个人任务')
                    break
                case 'team':
                    innerRoute.push('团队任务')
                    break
                default:
                    return ''
            }

            if(res.path.length === 3) return innerRoute
            switch(res.path[3]) {
                case 'detail':
                    const taskId = getParam(res.params, 'taskId')
                    if(taskId === undefined) return ''

                    const task = taskList.value.find(task => Number(task.id) === Number(taskId))
                    if(!task) return ''

                    let prefix = task.team === null ? '个人' : '团队';
                    innerRoute.push(prefix + '任务\"' + task.title + '\"的详情')

                    if(res.path.length  > 4) return ''
                    return innerRoute
                case 'edit':
                    if(innerRoute[0] === '团队任务') return ''
                    const isNew = getParam(res.params, 'isNew')
                    if(isNew === undefined) return ''

                    if(isNew === 'true') innerRoute.push('新建个人任务')
                    else {
                        const taskId = getParam(res.params, 'taskId')
                        if(taskId === undefined) return ''

                        const task = taskList.value.find(task => Number(task.id) === Number(taskId))
                        if(!task) return ''
                        innerRoute.push('编辑个人任务\"' + task.title + '\"')
                    }
                    if(res.path.length > 4) return ''
                    return innerRoute
                default:
                    return ''
            }
        case 'team':
            if(res.path.length <= 2) return ''
            switch(res.path[2]) {
                case 'all':
                    innerRoute.push('全部团队')
                    break
                case 'owner':
                    innerRoute.push('我拥有的团队')
                    break
                case 'admin':
                    innerRoute.push('我管理的团队')
                    break
                case 'member':
                    innerRoute.push('我参与的团队')
                    break
                default:
                    return ''
            }

            if(res.path.length === 3) return innerRoute
            switch(res.path[3]) {
                case 'space':
                    const teamId = getParam(res.params, 'teamId')
                    if(teamId === undefined) return ''
                    const team = teamList.value.find(team=> Number(team.id) === Number(teamId))
                    if(!team) return ''
                    innerRoute.push(team.title + '的团队空间')

                    if(res.path.length === 4) return innerRoute
                    switch(res.path[4]) {
                        case 'detail':
                            const taskId = getParam(res.params, 'taskId')
                            if(taskId === undefined) return ''

                            const task = taskList.value.find(task => Number(task.id) === Number(taskId))
                            if(!task) return ''
                            innerRoute.push('团队任务\"' + task.title + '\"的详情')

                            if(res.path.length  > 5) return ''
                            return innerRoute
                        case 'edit':
                            const isNew = getParam(res.params, 'isNew')
                            if(isNew === undefined) return ''

                            if(isNew === 'true') innerRoute.push('新建团队任务')
                            else {
                                const taskId = getParam(res.params, 'taskId')
                                if(taskId === undefined) return ''

                                const task = taskList.value.find(task => Number(task.id) === Number(taskId))
                                if(!task) return ''
                                innerRoute.push('编辑团队任务\"' + task.title + '\"')
                            }
                            if(res.path.length > 5) return ''
                            return innerRoute
                        case 'personnel':
                            if(team.owner === currentUser.username) innerRoute.push('编辑成员信息')
                            else innerRoute.push('成员信息')

                            if(res.path.length > 5) return ''
                            return innerRoute
                        default:
                            return ''
                    }
                default:
                    return ''
            }
        case 'settings':
            if(res.path.length <= 2) return ''
            switch(res.path[2]) {
                case 'info':
                    innerRoute.push('个人资料')
                    if(res.path.length > 3) return ''
                    return innerRoute
                default:
                    return ''
            }
        default:
            return ''
    }
}