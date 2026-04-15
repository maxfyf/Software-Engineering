import { useRouter, useRoute } from 'vue-router'

/**
 * 团队视图的通用逻辑
 * @param {Function|null} filterFn - 团队筛选函数
 * @param {string} pageTitle - 页面标题
 */
export function useTeamView(filterFn = null, pageTitle = '全部团队') {
    const router = useRouter()
    const route = useRoute()

    // TODO:团队结构体数组teams
    let teams = []

    // TODO: 团队名字符串数组dataset（建议重构为taskNames和teamNames）
    let dataset = []

    // TODO: 下拉框中选择团队进入团队空间的回调函数handleSelect（建议重构为handleSelectTask和handleSelectTeam)
    let handleSelect = () => {

    }

    // TODO: 创建新团队的函数handleNew（建议重构为handleNewTask和handleNewTeam)
    let handleNew = () => {

    }

    // TODO: 进入团队空间页面的函数handleEnterTeamSpace
    let handleEnterTeamSpace = () => {

    }

    return {
        teams,
        dataset,
        router,
        handleSelect,
        handleNew,
        handleEnterTeamSpace
    }
}