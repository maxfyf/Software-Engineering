<script setup lang="js">
import { ref, computed, onMounted } from 'vue';
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Search from "@/components/Search.vue";
import TaskList from "@/components/TaskList.vue";
import TaskDetail from "@/components/TaskDetail.vue";
import { taskList, highlightTaskId, initTaskList } from '@/store/user.js';
import { useRouter } from 'vue-router';
import { Plus } from "@element-plus/icons-vue";

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  filterFn: {
    type: Function,
    default: null
  },
  showNewButton: {
    type: Boolean,
    default: false
  }
})

const router = useRouter();

// 根据 filterFn 筛选任务
const tasks = computed(() => {
  if (props.filterFn) {
    return taskList.value.filter(props.filterFn)
  }
  return taskList.value
})

// 搜索数据集
const dataset = computed(() => tasks.value.map(task => task.title))

// 页面加载时获取任务列表
onMounted(async () => {
  await initTaskList()
})

// 分页状态
const currentPage = ref(1)
const pageSize = ref(10)

// 详情弹窗状态
const viewDialogVisible = ref(false)
const currentTask = ref(null)

// 搜索选中任务
const handleSelect = (taskName) => {
  console.log('选中任务:', taskName)
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
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <span class="route">{{ title }}</span>
        <div class="search-wrapper">
          <Search :data="dataset" :onSelect="handleSelect" />
        </div>
      </div>
    </template>

    <div class="main-content-wrapper">
      <div v-if="showNewButton" class="header">
        <el-button type="primary" class="new-button" @click="handleNew">
          <el-icon><Plus/></el-icon>
          &nbsp;新建
        </el-button>
      </div>
      <div v-else class="header-spacer" />

      <TaskList
          :tasks="tasks"
          :router="router"
          :current-page="currentPage"
          :page-size="pageSize"
          @page-change="handlePageChange"
          @view-detail="handleViewDetail"
      />
    </div>

    <TaskDetail
        :current-task="currentTask"
        v-model:visible="viewDialogVisible"
    />
  </HeaderWrapper>
</template>

<style scoped>
.inner-header {
  left: 0;
  right: 0;
  top: 0;
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
}

.route {
  display: inline-flex;
  height: 100%;
  align-items: center;
  font-size: 20px;
  font-weight: bold;
  color: #333333;
}

.search-wrapper {
  display: flex;
  position: absolute;
  right: 20px;
  width: 250px;
  align-items: center;
}

.main-content-wrapper {
  margin-top: 20px;
  margin-left: 20px;
  margin-right: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.header {
  width: 100%;
  display: flex;
}

.header-spacer {
  width: 100%;
  height: 15px;
}

.new-button {
  width: 70px;
  margin-left: auto;
  margin-right: 15px;
}

:deep(.el-pagination .el-pager li) {
  background-color: transparent !important;
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  background-color: transparent !important;
  color: black !important;
}
</style>