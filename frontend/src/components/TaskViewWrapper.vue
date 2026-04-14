<script setup lang="js">
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Search from "@/components/Search.vue";
import TaskList from "@/components/TaskList.vue";
import TaskDetail from "@/components/TaskDetail.vue";
import { useTaskView } from '@/utils/useTaskView.js';
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

const {
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
} = useTaskView(props.filterFn, props.title)
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
          &nbsp;新建个人任务
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
  width: 120px;
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