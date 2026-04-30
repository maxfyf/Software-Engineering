// 路由解析器
const routeManager = (route) => {
    let path = route.split('/')
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
            console.log('param=', param)
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
    const res = routeManager(route)
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
    console.log(params)
    router.push({
        path: newRoute,
        query: queryObj
    })
    return true
}

// 退出页面
export const handleBack = (route, router, num) => {
    if(num <= 0) return false
    const res = routeManager(route)
    if(!res || res.path.length <= num) return false

    res.path.length -= num
    const newRoute = res.path.join('/')

    // 根据需要可继续扩展
    let keys = new Set()
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