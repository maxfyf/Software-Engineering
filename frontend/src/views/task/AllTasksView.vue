<script setup lang="js">
import { ref, computed, onMounted } from 'vue';
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Search from "@/components/Search.vue";
import TaskList from "@/components/TaskList.vue";
import TaskDetail from "@/components/TaskDetail.vue";
import { taskList, highlightTaskId, initTaskList } from '@/store/user.js';
import { useRouter } from 'vue-router';

const router = useRouter();

// 实际用户所有任务名称字符串数组
// TODO: 改为用户可见的所有任务，通过taskList实现，且任务结构体添加权限等级（ReadOnly/Participate/Administrate）
const tasks = computed(

)

// TODO: 改成tasks中每一项的title
const dataset = computed(() => taskList.value.map(task => task.title))

// 页面加载时获取任务列表
onMounted(async () => {
  await initTaskList()
})

const currentPage = ref(1)    // 当前数据页
const pageSize = ref(10)    // 每页数据条数
const viewDialogVisible = ref(false)    // 查看任务窗口是否可见
const currentTask = ref(null)           // 当前查看的任务

// 实际选中选项后的回调函数（切换页面到指定任务对应的页面）
const handleSelect = (taskName) => {
  console.log('选中任务:', taskName)
  const task = taskList.value.find(t => t.title === taskName)
  if (task) {
    // 找到任务在列表中的索引
    const index = taskList.value.findIndex(t => t.id === task.id)
    // 切换到该任务所在的页面
    currentPage.value = Math.floor(index / pageSize.value) + 1
    
    highlightTaskId.value = task.id

    currentTask.value = task
    viewDialogVisible.value = true
  }
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

    <TaskList
        :tasks="tasks"
        :router="router"
        :current-page="currentPage.value"
        :pageSize="pageSize.value"
        :currentTask="currentTask.value"
        :viewDialogVisible="viewDialogVisible.value"
    />

    <TaskDetail
        :currentTask="currentTask.value"
        :viewDialogVisible="viewDialogVisible.value"
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
</style>
