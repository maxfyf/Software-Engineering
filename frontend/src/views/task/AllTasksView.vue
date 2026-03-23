<script setup lang="js">
import { ref, computed } from 'vue';
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Search from "@/components/Search.vue";
import { Plus, View, Edit, Delete } from "@element-plus/icons-vue";

// TODO: 改成实际用户所有任务名称字符串数组
const dataset = ['apple', 'banana', 'pear', 'peach']

// TODO: 改成实际选中选项后的回调函数（切换页面到指定任务对应的页面）
const handleSelect = () => {}

// TODO: 任务数据，可直接使用原始taskInfo数组，程序将根据taskInfo结构体中的prop名自动填表
const data1 = {
  title: "task1",
  status: "进行中",
  priority: "高"
};
const data2 = {
  title: "task2",
  status: "待办",
  priority: "中"
}
const taskData = ref([data1, data2]);

// TODO: 新建任务
const handleNew = () => {

}

const viewDialogVisible = ref(false)    // 查看任务窗口是否可见

const closeViewDialog = () => {
  viewDialogVisible.value = false
}

const viewDetail = () => {
  viewDialogVisible.value = true
  // TODO: 查看任务详情

}

// TODO: 编辑任务
const editTask = () => {

}

// TODO: 删除任务
const deleteTask = () => {

}

const currentPage = ref(1)    // 当前数据页
const pageSize = ref(10)    // 每页数据条数
const total = computed(() => taskData.value.length)    // 总数据条数
const pageData = computed(() => {    // 当前页面数据
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return taskData.value.slice(start, end)
})

// 切换页面
const handleCurrentChange = (page) => {
  currentPage.value = page
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
          <el-table :data="pageData" stripe class="task-table">
            <el-table-column prop="title" label="任务名称" min-width="50%" align="left" />
            <el-table-column prop="status" label="状态" min-width="20%" align="center" />
            <el-table-column prop="priority" label="优先级" min-width="15%" align="center" />
            <el-table-column fixed="right" label="操作" min-width="15%" align="center">
              <template v-slot:default="scope">
                <el-button link type="text" @click="viewDetail">
                  <el-icon>
                    <View/>
                  </el-icon>
                </el-button>

                <el-button link type="text" @click="editTask">
                  <el-icon>
                    <Edit/>
                  </el-icon>
                </el-button>

                <el-button link type="text" class="delete-button" @click="deleteTask">
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
        <p class="dialog-content"><span class="key">任务标题：</span>TODO</p>
        <p class="dialog-content"><span class="key">描述：</span>TODO</p>
        <p class="dialog-content"><span class="key">状态：</span>TODO</p>
        <p class="dialog-content"><span class="key">优先级：</span>TODO</p>
        <p class="dialog-content"><span class="key">截止时间：</span>TODO</p>
        <p class="dialog-content"><span class="key">创建时间：</span>TODO</p>
        <p class="dialog-content"><span class="key">更新时间：</span>TODO</p>
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
</style>