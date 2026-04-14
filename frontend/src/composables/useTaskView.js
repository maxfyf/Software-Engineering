import { ref, computed, onMounted } from 'vue'
import { taskList, highlightTaskId, initTaskList } from '@/store/user.js'
import { useRouter } from 'vue-router'

/**
 * 任务视图的通用逻辑
 * @param {Function|null} filterFn - 任务筛选函数
 */
export function useTaskView(filterFn = null) {
  const router = useRouter()

  // 根据 filterFn 筛选任务
  const tasks = computed(() => {
    if (filterFn) {
      return taskList.value.filter(filterFn)
    }
    return taskList.value
  })

  // 搜索数据集
  const dataset = computed(() => tasks.value.map(task => task.title))

  // 分页状态
  const currentPage = ref(1)
  const pageSize = ref(10)

  // 详情弹窗状态
  const viewDialogVisible = ref(false)
  const currentTask = ref(null)

  // 初始化
  onMounted(async () => {
    await initTaskList()
  })

  // 搜索选中任务
  const handleSelect = (taskName) => {
    const task = tasks.value.find(t => t.title === taskName)
    if (task) {
      const index = tasks.value.findIndex(t => t.id === task.id)
      currentPage.value = Math.floor(index / pageSize.value) + 1
      highlightTaskId.value = task.id
      currentTask.value = task
      viewDialogVisible.value = true
    }
  }

  // 新建任务
  const handleNew = () => {
    router.push({
      path: '/task/edit',
      query: { isNew: 'true' }
    })
  }

  // 分页变化
  const handlePageChange = (page) => {
    currentPage.value = page
  }

  // 查看详情
  const handleViewDetail = (task) => {
    currentTask.value = task
    viewDialogVisible.value = true
  }

  return {
    tasks,
    dataset,
    currentPage,
    pageSize,
    viewDialogVisible,
    currentTask,
    router,
    handleSelect,
    handleNew,
    handlePageChange,
    handleViewDetail
  }
}