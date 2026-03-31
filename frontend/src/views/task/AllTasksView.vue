<script setup lang="js">
import { ref, computed, onMounted } from 'vue';
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Search from "@/components/Search.vue";
import { Plus, View, Edit, Delete } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from 'element-plus';
import { useRouter } from 'vue-router';
import { taskList, highlightTaskId,removeTask, initTaskList } from '@/store/user.js';

const router = useRouter();
// 实际用户所有任务名称字符串数组
const dataset = computed(() => taskList.value.map(task => task.title))

// 页面加载时获取任务列表
onMounted(async () => {
  await initTaskList()
})

// 实际选中选项后的回调函数（切换页面到指定任务对应的页面）
const handleSelect = (taskName) => {
  console.log('选中任务:', taskName)
  const task = taskList.value.find(t => t.title === taskName)
  if (task) {
    // 找到任务在列表中的索引
    const index = taskList.value.findIndex(t => t.id === task.id)
    // 计算该任务所在的页码
    const targetPage = Math.floor(index / pageSize.value) + 1
    // 切换到对应页面
    currentPage.value = targetPage
    
    highlightTaskId.value = task.id

    currentTask.value = task
    viewDialogVisible.value = true
  }
}

// 表格行样式回调
const tableRowClassName = ({ row }) => {
  if (row.id === highlightTaskId.value) {
    return 'highlight-row'
  }
  return ''
}

// 新建任务
const handleNew = () => {
  console.log('新建任务')
  // 跳转到编辑页面，并传递 isNew 参数
  router.push({
    path: '/task/edit',
    query: { isNew: 'true' }
  })
}

const viewDialogVisible = ref(false)    // 查看任务窗口是否可见
const currentTask = ref(null)           // 当前查看的任务

const closeViewDialog = () => {
  viewDialogVisible.value = false
}

const viewDetail = (row) => {
  currentTask.value = row
  highlightTaskId.value = row.id
  viewDialogVisible.value = true
}

// 编辑任务
const editTask = (row) => {
  console.log('编辑任务:', row)
  highlightTaskId.value = row.id
  // 跳转到编辑页面，传递任务ID
  router.push({
    path: '/task/edit',
    query: { 
      isNew: 'false',
      taskId: row.id 
    }
  })
}

// 删除任务
const deleteTask = (row) => {
  highlightTaskId.value = null
  ElMessageBox.confirm(
    `确定要删除任务"${row.title}"吗？`,
    '',
    {
      confirmButtonText: '确定',
      confirmButtonType: 'danger',
      cancelButtonText: '取消',
      type: undefined
    }
  ).then(() => {
    removeTask(row.id)
    ElMessage.success('任务已删除')
  }).catch(() => {
    console.log('取消删除')
  })
}

const currentPage = ref(1)    // 当前数据页
const pageSize = ref(10)    // 每页数据条数
const total = computed(() => taskList.value.length)    // 总数据条数
const pageData = computed(() => {    // 当前页面数据
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return taskList.value.slice(start, end)
})

// 切换页面
const handleCurrentChange = (page) => {
  currentPage.value = page
}


const formatDate = (dateStr) => {
  if (!dateStr) return '未设置'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}


</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <span class="route">全部任务</span>
        <div class="search-wrapper">
          <Search
              :data="dataset"
              :onSelect="handleSelect"
          />
        </div>
      </div>
    </template>

    <div class="main-content-wrapper">
      <div class="header">
        <el-button
            type="primary"
            class="new-button"
            @click="handleNew"
        >
          <el-icon>
            <Plus/>
          </el-icon>
          &nbsp;新建
        </el-button>
      </div>

      <el-row>
        <el-col>
          <el-table :data="pageData" stripe class="task-table" :row-class-name="tableRowClassName">
            <el-table-column prop="title" label="任务名称" min-width="50%" align="left" />
            <el-table-column prop="status" label="状态" min-width="20%" align="center" />
            <el-table-column prop="priority" label="优先级" min-width="15%" align="center" />
            <el-table-column fixed="right" label="操作" min-width="15%" align="center">
              <template v-slot:default="scope">
                <el-button link type="text" @click="viewDetail(scope.row)">
                  <el-icon>
                    <View/>
                  </el-icon>
                </el-button>

                <el-button link type="text" @click="editTask(scope.row)">
                  <el-icon>
                    <Edit/>
                  </el-icon>
                </el-button>

                <el-button link type="text" class="delete-button" @click="deleteTask(scope.row)">
                  <el-icon>
                    <Delete/>
                  </el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-col>
      </el-row>

      <el-pagination
          @current-change="handleCurrentChange"
          :current-page="currentPage"
          :page-size="pageSize"
          layout="prev, pager, next"
          :total="total"
          class="pagination"
      />
    </div>

    <el-dialog
        v-model="viewDialogVisible"
        width="500px"
        center
        :before-close="closeViewDialog"
    >
      <template #header>
        <span class="dialog-title">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;任务详情</span>
      </template>
      <div class="dialog-content-wrapper">
        <p class="dialog-content">
          <span class="key">任务标题：</span>
          {{ currentTask.title }}
        </p>
        <p class="dialog-content" v-if="currentTask.description !== ''">
          <span class="key">描述：</span>
          {{ currentTask.description }}
        </p>
        <p class="dialog-content">
          <span class="key">状态：</span>
          {{ currentTask.status }}
        </p>
        <p class="dialog-content">
          <span class="key">优先级：</span>
          {{ currentTask.priority }}
        </p>
        <p class="dialog-content" v-if="currentTask.deadline !== null">
          <span class="key">截止时间：</span>
          {{ currentTask.deadline }}
        </p>
        <p class="dialog-content">
          <span class="key">创建时间：</span>
          {{ formatDate(currentTask.createdAt) }}
        </p>
        <p class="dialog-content">
          <span class="key">更新时间：</span>
          {{ formatDate(currentTask.updatedAt) }}
        </p>
      </div>
    </el-dialog>
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

.new-button {
  width: 70px;
  margin-left: auto;
  margin-right: 15px;
}

.task-table {
  width: 100%;
  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
}

.delete-button:hover {
  color: #f56c6c !important;
}

.pagination {
  display: flex;
  justify-content: flex-end;
}

:deep(.el-pagination .el-pager li) {
  background-color: transparent !important;
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  background-color: transparent !important;
  color: black !important;
}

.dialog-title {
  color: black;
  font-weight: bold;
  font-size: 20px;
}

.dialog-content-wrapper {
  overflow-y: auto;
  max-height: 400px;
}

.dialog-content {
  padding: 0 20px;
  font-size: 18px;
}

.key {
  font-weight: bold;
}

:deep(.el-table__row.highlight-row) {
  background-color: #ecf5ff !important;
}

:deep(.el-table__row.highlight-row td) {
  background-color: #ecf5ff !important;
}

:deep(.el-table__row--striped.highlight-row) {
  background-color: #ecf5ff !important;
}

:deep(.el-table__row--striped.highlight-row td) {
  background-color: #ecf5ff !important;
}

</style>
