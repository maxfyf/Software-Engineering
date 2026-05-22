import { ref, computed, onMounted } from 'vue'
import { taskList, highlightTaskId, initTaskList } from '@/store/user.js'
import { useRouter, useRoute } from 'vue-router'
import {handleEnter} from "@/utils/routeManager.js";

export function useTaskView(filterFn = null) {
  const router = useRouter()
  const route = useRoute()

  // 根据 filterFn 筛选任务
  const tasks = computed(() => {
    if (filterFn) {
      return taskList.value.filter(filterFn)
    }
    return taskList.value
  })

  // 搜索数据集，同名任务需要区分显示
  const dataset = computed(() => {
    return tasks.value.map(task => {
      if (task.team) {
        // 团队任务
        return { data: `${task.title}`, aux: `${task.team}` }
      } else {
        // 个人任务
        return { data: `${task.title}`, aux: `个人` }
      }
    })
  })

  // 分页状态
  const currentPage = ref(1)
  const pageSize = ref(10)

  // 初始化任务列表
  onMounted(async () => {
    await initTaskList(false)
  })

  // 搜索选中任务
  const handleSelect = (displayText) => {
    // 解析显示文本：格式为 "任务名 (团队名)" 或 "任务名 (个人)"
    const match = displayText.match(/^(.+) \((.+)\)$/)
    if (!match) return

    const title = match[1]
    const teamInfo = match[2]

    // 根据团队信息匹配正确的任务
    const task = tasks.value.find(t => {
      if (teamInfo === '个人') {
        return t.title === title && t.team === null
      } else {
        return t.title === title && t.team === teamInfo
      }
    })

    if (task) {
      const index = tasks.value.findIndex(t => t.id === task.id)
      currentPage.value = Math.floor(index / pageSize.value) + 1
      highlightTaskId.value = task.id
    }
  }

  // 新建任务
  const handleNew = () => {
    const newPage = {
      path: 'edit',
      params: [
        {
          key: 'isNew',
          value: true
        }
      ]
    }
    handleEnter(route, router, newPage)
  }

  // 分页变化
  const handlePageChange = (page) => {
    currentPage.value = page
  }

  return {
    tasks,
    dataset,
    currentPage,
    pageSize,
    handleSelect,
    handleNew,
    handlePageChange
  }
}