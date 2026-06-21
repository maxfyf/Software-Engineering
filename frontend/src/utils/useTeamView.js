import { ref, computed, onMounted } from 'vue'
import { teamList, disbandedTeamList, highlightTeamId, addTeam, initTeamList, initDisbandedTeamList, renameTeam, restoreTeam } from '@/store/user.js'
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

    // 团队名字符串数组dataset
    const dataset = computed(() => {
        return teams.value.map(team => {
            return { data: team.title, aux: '' }
        })
    })

    // 新建/重命名团队弹窗状态
    const createDialogVisible = ref(false)
    const renameDialogVisible = ref(false)
    const currentTeam = ref(null)
    const newTeamTitle = ref('')
    const renameTeamTitle = ref('')

    // 初始化团队列表
    onMounted(async () => {
        await initTeamList()
    })

    // 下拉框中选择团队进入团队空间的回调函数handleSelect
    const handleSelect = (selectedItem) => {
        const teamTitle = selectedItem?.data
        const team = teams.value.find(t => t.title === teamTitle)
        if (team) {
            highlightTeamId.value = team.id
            handleEnterTeamSpace(team.id)
        }
    }

    // 创建新团队
    const handleNew = () => {
        createDialogVisible.value = true
        newTeamTitle.value = ''
    }

    // 重命名团队
    const handleRename = (team) => {
        renameDialogVisible.value = true
        currentTeam.value = team
        renameTeamTitle.value = team.title
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

    // 确认重命名团队
    const handleRenameTeam = async () => {
        if (!renameTeamTitle.value || renameTeamTitle.value.trim() === '') {
            ElMessage.error('新团队名称不能为空')
            return
        }

        const trimmedTitle = renameTeamTitle.value.trim()
        if (trimmedTitle.length > 10) {
            ElMessage.error('新团队名称长度不能超过10个字符')
            return
        }

        try {
            await renameTeam(currentTeam.value.id, trimmedTitle)
            ElMessage.success('团队已重命名')
            renameDialogVisible.value = false
            currentTeam.value = null
            renameTeamTitle.value = ''
        } catch (error) {
            console.error('重命名团队失败:', error)
        }
    }

    // 取消重命名团队
    const handleCancelRename = () => {
        renameDialogVisible.value = false
        currentTeam.value = null
        renameTeamTitle.value = ''
    }

    const disbandedTeams = computed(() => disbandedTeamList.value)

    const activeTeamTitleSet = computed(() => new Set(teamList.value.map(team => team.title)))

    const hasActiveTeamTitle = (title) => activeTeamTitleSet.value.has(title)

    const loadDisbandedTeams = async (force = false) => {
        await initDisbandedTeamList(force)
    }

    const handleRestoreTeam = async (team) => {
        await restoreTeam(team.id)
        ElMessage.success(`团队「${team.title}」已恢复`)
    }
    // 进入回收站
    const handleEnterDisbandedTeamsPage = () => {
        const newPage = {
            path: 'disbanded',
            params: []
        }
        handleEnter(route, router, newPage)
    }

    // 进入团队空间页面
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
        renameDialogVisible,
        newTeamTitle,
        renameTeamTitle,
        disbandedTeams,
        hasActiveTeamTitle,
        loadDisbandedTeams,
        handleRestoreTeam,
        handleSelect,
        handleNew,
        handleRename,
        handleCreateTeam,
        handleCancelCreate,
        handleRenameTeam,
        handleCancelRename,
        handleEnterDisbandedTeamsPage,
        handleEnterTeamSpace
    }
}