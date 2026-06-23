import { getUserProfile, userProfileMap } from "@/store/user.js";

export function profileLoader() {
    const getPrimaryAssignee = (task) => {
        const assignees = Array.isArray(task.assignee) ? task.assignee : (task.assignee ? [task.assignee] : [])
        return assignees[0] || ''
    }

    const loadAssigneeProfile = async (task) => {
        const username = getPrimaryAssignee(task)
        if (!username || userProfileMap[username]) return

        try {
            await getUserProfile(username)
        } catch (error) {
            console.error('获取负责人信息失败:', error)
        }
    }

    const getAssigneeProfile = (task) => {
        const username = getPrimaryAssignee(task)
        return username ? userProfileMap[username] : null
    }

    return {
        getPrimaryAssignee,
        loadAssigneeProfile,
        getAssigneeProfile
    }
}