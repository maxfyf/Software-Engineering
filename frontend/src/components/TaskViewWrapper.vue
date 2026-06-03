<script setup lang="js">
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Route from "@/components/Route.vue";
import Search from "@/components/Search.vue";
import TaskList from "@/components/TaskList.vue";
import { useTaskView } from '@/utils/useTaskView.js';
import { useRoute, useRouter } from "vue-router";
import { Plus } from "@element-plus/icons-vue";
import { handleEnter } from "@/utils/routeManager.js";

const props = defineProps({
  filterFn: {
    type: Function,
    default: null
  },
  showNewButton: {
    type: Boolean,
    default: false
  },
  showAssignee: {
    type: Boolean,
    default: false
  },
  isTeamSpace: {
    type: Boolean,
    default: false
  },
  isAdmin: {
    type: Boolean,
    default: false
  },
  showAux: {
    type: Boolean,
    default: false
  },
  isPersonal: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()
const router = useRouter()

const {
  tasks,
  dataset,
  currentPage,
  pageSize,
  handleSelect,
  handleNew,
  handlePageChange
} = useTaskView(props.filterFn)

const handleSelectTask = (selectedItem) => {
  const task = handleSelect(selectedItem)
  // 跳转到选中任务的详情页面
  if (task) {
    const newPage = {
      path: 'detail',
      params: [
        {
          key: 'taskId',
          value: task.id
        }
      ]
    }
    handleEnter(route, router, newPage)
  }
}

// 查看个人任务相关的操作日志
const handleViewOperations = () => {
  // TODO
}
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <div class="route-wrapper">
          <Route :route="route" :router="router" />
        </div>

        <div class="search-wrapper">
          <Search :dataset="dataset" :onSelect="handleSelectTask" :showAux="showAux" />
        </div>
      </div>
    </template>

    <div class="main-content-wrapper">
      <div v-if="showNewButton" class="header">
        <el-button type="primary" class="new-button" @click="handleNew">
          <el-icon><Plus/></el-icon>
          <span v-if="showAssignee === false">
              &nbsp;新建个人任务
            </span>
          <span v-else>
              &nbsp;新建团队任务
            </span>
        </el-button>
      </div>
      <div v-else class="header-spacer" />

      <TaskList
          :tasks="tasks"
          :show-assignee="showAssignee"
          :is-admin="isAdmin"
          :is-team-space="isTeamSpace"
          :current-page="currentPage"
          :page-size="pageSize"
          @page-change="handlePageChange"
      />

      <div v-if="isPersonal" class="footer">
        <el-button type="primary" class="operation-button" @click="handleViewOperations">
          查看操作日志
        </el-button>
      </div>
    </div>
  </HeaderWrapper>
</template>

<style scoped>
.route-wrapper {
  display: flex;
  left: 20px;
  align-items: center;
}

.search-wrapper {
  display: flex;
  position: absolute;
  right: 20px;
  width: 250px;
  align-items: center;
}

.main-content-wrapper {
  margin: 20px;
  height: calc(100% - 40px);
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
  width: 128px;
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

.footer {
  width: 100%;
  height: 35px;
  margin-top: auto;
  margin-bottom: 20px;
  display: flex;
  flex-direction: row;
  justify-content: center;
}

.operation-button {
  width: 200px;
  height: 100%;
  font-size: 20px;
}
</style>