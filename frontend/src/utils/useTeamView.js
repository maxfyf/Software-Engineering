import { ref, computed, onMounted } from 'vue'
import { teamList, highlightTeamId, addTeam, initTeamList } from '@/store/user.js'
import { useRoute, useRouter } from 'vue-router'
import { handleEnter } from "@/utils/routeManager.js";
import { ElMessage } from 'element-plus';

export function useTeamView(filterFn = null) {
    const route = useRoute()
    const router = useRouter()

    // 根据 filterFn 筛选团队
    const teams = computed(() => {
        if (filterFn) {
            return teamList.value.filter(filterFn)
        }
        return teamList.value
    })

    // 团队名字符串数组dataset（建议重构为taskNames和teamNames）
    const dataset = computed(() => teams.value.map(team => team.title))

    // 新建团队弹窗状态
    const createDialogVisible = ref(false)
    const newTeamTitle = ref('')

    // 初始化团队列表
    onMounted(async () => {
        await initTeamList()
    })

    // 下拉框中选择团队进入团队空间的回调函数handleSelect（建议重构为handleSelectTask和handleSelectTeam)
    const handleSelect = (teamTitle) => {
        const team = teams.value.find(t => t.title === teamTitle)
        if (team) {
            highlightTeamId.value = team.id
        }
    }

    // 创建新团队的函数handleNew（建议重构为handleNewTask和handleNewTeam)
    const handleNew = () => {
        createDialogVisible.value = true
        newTeamTitle.value = ''
    }

    // 确认创建团队
    const handleCreateTeam = async () => {
        if (!newTeamTitle.value || newTeamTitle.value.trim() === '') {
            ElMessage.error('团队名称不能为空')
            return
        }

        const trimmedTitle = newTeamTitle.value.trim()
        if (trimmedTitle.length > 10) {
            ElMessage.error('团队名称长度不能超过10个字符')
            return
        }

        try {
            await addTeam({
                title: trimmedTitle
            })
            createDialogVisible.value = false
            newTeamTitle.value = ''
        } catch (error) {
            console.error('创建团队失败:', error)
        }
    }

    // 取消创建团队
    const handleCancelCreate = () => {
        createDialogVisible.value = false
        newTeamTitle.value = ''
    }

    // 进入团队空间页面的函数handleEnterTeamSpace
    const handleEnterTeamSpace = (teamId) => {
        highlightTeamId.value = teamId
        const newPage = {
            path: 'space',
            params: [
                {
                    key: 'teamId',
                    value: teamId
                }
            ]
        }
        handleEnter(route, router, newPage)
    }

    return {
        teams,
        dataset,
        createDialogVisible,
        newTeamTitle,
        handleSelect,
        handleNew,
        handleCreateTeam,
        handleCancelCreate,
        handleEnterTeamSpace
    }
}