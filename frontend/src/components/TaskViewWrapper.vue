<script setup lang="js">
import { computed } from 'vue'
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Search from "@/components/Search.vue";
import TaskList from "@/components/TaskList.vue";
import TaskDetail from "@/components/TaskDetail.vue";
import { useTaskView } from '@/utils/useTaskView.js';
import { Back, Plus } from "@element-plus/icons-vue";
import { useRoute, useRouter } from "vue-router";

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
  extraQuery: {
    type: Object,
    default: () => ({})
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
} = useTaskView(props.filterFn, props.title, props.extraQuery)

const route = useRoute()

// 从路由路径获取父页面名称
const parentPageName = computed(() => {
  const path = route.path
  if (path.includes('/team/all/')) return 'all'
  if (path.includes('/team/owner/')) return 'owner'
  if (path.includes('/team/admin/')) return 'admin'
  if (path.includes('/team/member/')) return 'member'
  return ''
})

const parentPageTitle = computed(() => {
  const path = route.path
  if (path.includes('/team/all/')) return '全部团队'
  if (path.includes('/team/owner/')) return '我拥有的团队'
  if (path.includes('/team/admin/')) return '我管理的团队'
  if (path.includes('/team/member/')) return '我参与的团队'
  return ''
})

const goToParentPage = () => {
  router.push({
    path: `/team/${parentPageName.value}`,
  })
}
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <el-button
            v-if="isTeamSpace"
            link
            type="text"
            size="large"
            @click="goToParentPage"
        >
          <el-icon :size="25">
            <Back/>
          </el-icon>
        </el-button>
        <span class="route">
          <span
              v-if="isTeamSpace"
              class="clickable"
              @click="goToParentPage"
          >
            {{ parentPageTitle }}
          </span>
          <span v-if="isTeamSpace">&nbsp;>&nbsp;</span>
          <span class="present-directory">
            {{ title }}
          </span>
        </span>
        <div class="search-wrapper">
          <Search :data="dataset" :onSelect="handleSelect" />
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
          :router="router"
          :show-assignee="showAssignee"
          :is-admin="isAdmin"
          :current-page="currentPage"
          :page-size="pageSize"
          @page-change="handlePageChange"
          @view-detail="handleViewDetail"
      />
    </div>

    <TaskDetail
        :current-task="currentTask"
        :show-assignee="showAssignee"
        v-model:visible="viewDialogVisible"
    />
  </HeaderWrapper>
</template>

<style scoped>
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
</style>