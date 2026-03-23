<script setup lang="js">
import { ref, computed } from 'vue';
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Search from "@/components/Search.vue"
import { Plus, View, Delete } from "@element-plus/icons-vue";

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
  status: "新建",
  priority: "中"
}
const taskData = ref([data1, data2]);

// TODO: 新建任务
const handleNew = () => {

}

//TODO: 查看任务详情
const viewDetail = () => {

}

//TODO: 删除任务
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
                <el-button link type="primary" @click="viewDetail">
                  <el-icon>
                    <View/>
                  </el-icon>
                </el-button>
                <el-button link type="danger" @click="deleteTask">
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
  box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2)
}

.pagination {
  display: flex;
  justify-content: flex-end;
}
</style>