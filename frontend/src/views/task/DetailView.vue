<script setup lang="js">
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { handleBack } from "@/utils/routeManager.js";
import { getTaskById, getPredecessors, getSuccessors } from "@/store/user.js";
import Route from "@/components/Route.vue";
import HeaderWrapper from "@/components/HeaderWrapper.vue";

const route = useRoute()
const router = useRouter()
const routeRef = ref(null)

const task = ref(null)
const predecessorTasks = ref([])
const successorTasks = ref([])

const loadTaskDetail = async (taskId) => {
  if (!taskId) {
    task.value = null
    predecessorTasks.value = []
    successorTasks.value = []
    return
  }

  task.value = await getTaskById(taskId)

  if (!task.value) {
    predecessorTasks.value = []
    successorTasks.value = []
    return
  }

  const predecessors = await getPredecessors(task.value.id)
  predecessorTasks.value = predecessors.map(pred => ({
    id: pred.id,
    title: pred.title,
    status: pred.status
  }))

  const successors = await getSuccessors(task.value.id)
  successorTasks.value = successors.map(succ => ({
    id: succ.id,
    title: succ.title,
    status: succ.status
  }))
}

watch(
  () => route.query.taskId,
  (taskId) => loadTaskDetail(Number(taskId)),
  { immediate: true }
)

const viewPredecessorDetail = async (index) => {
  const predTask = predecessorTasks.value[index]
  if (!predTask) return
  // 跳转到前置任务的详情页面
  await router.push({
    path: route.path,
    query: {
      ...route.query,
      taskId: predTask.id
    }
  })
  await routeRef.value?.refreshRoute()
}

const viewSuccessorDetail = async (index) => {
  const succTask = successorTasks.value[index]
  if (!succTask) return
  // 跳转到后继任务的详情页面
  await router.push({
    path: route.path,
    query: {
      ...route.query,
      taskId: succTask.id
    }
  })
  await routeRef.value?.refreshRoute()
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
        <Route ref="routeRef" :route="route" :router="router"/>
      </div>
    </template>

    <div class="main-content-wrapper">
      <el-card class="box-card">
        <div class="item-wrapper">
          <p class="item">
            <span class="key">任务标题：</span>
            <span class="content">
              {{ task?.title }}
            </span>
          </p>
          <p v-if="task?.team !== null" class="item">
            <span class="key">所属团队：</span>
            <span class="content">
              {{ task?.team }}
            </span>
          </p>
          <p v-if="task?.team !== null" class="item">
            <span class="key">负责人：</span>
            <span class="content">
              {{ Array.isArray(task?.assignee) ? task?.assignee.join(', ') : task?.assignee }}
            </span>
          </p>
          <p v-if="task?.description !== ''" class="item">
            <span class="key">描述：</span>
            <span class="content">
              {{ task?.description }}
            </span>
          </p>
          <p class="item">
            <span class="key">状态：</span>
            <span class="content">
              {{ task?.status }}
            </span>
          </p>
          <p class="item">
            <span class="key">优先级：</span>
            <span class="content">
              {{ task?.priority }}
            </span>
          </p>
          <p v-if="task?.deadline !== null" class="item">
            <span class="key">截止时间：</span>
            <span class="content">
              {{ task?.deadline }}
            </span>
          </p>
          <p class="item">
            <span class="key">创建时间：</span>
            <span class="content">
              {{ formatDate(task?.createdAt) }}
            </span>
          </p>
          <p class="item">
            <span class="key">更新时间：</span>
            <span class="content">
              {{ formatDate(task?.updatedAt) }}
            </span>
          </p>
          <div v-if="predecessorTasks.length > 0" class="item">
            <span class="key">前置任务：</span>
            <div class="content">
              <p
                  v-for="(item, index) in predecessorTasks"
                  :key="item.id"
                  class="clickable"
                  @click="viewPredecessorDetail(index)"
              >
                {{ item.title }}（{{ item.status }}）
              </p>
            </div>
          </div>
          <div v-if="successorTasks.length > 0" class="item">
            <span class="key">后继任务：</span>
            <div class="content">
              <p
                  v-for="(item, index) in successorTasks"
                  :key="item.id"
                  class="clickable"
                  @click="viewSuccessorDetail(index)"
              >
                {{ item.title }}（{{ item.status }}）
              </p>
            </div>
          </div>
        </div>

        <template #footer>
          <div class="footer">
            <el-button
                type="primary"
                class="back"
                @click="handleBack(route, router, 1)"
            >
              返回
            </el-button>
          </div>
        </template>
      </el-card>
    </div>
  </HeaderWrapper>
</template>

<style scoped>
.main-content-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.box-card {
  width: 90%;
  height: 90%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.item-wrapper {
  padding: 0 20px;
  overflow-x: visible;
}

.item {
  width: 100%;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  margin-top: 20px;
}

.key {
  flex-shrink: 0;
  font-size: 19px;
  font-weight: bold;
  text-align: center;
}

.content {
  font-size: 19px;
  word-break: break-word;
}

.clickable {
  cursor: pointer;
  color: #409eff;
  margin: 0;
  padding: 2px 0;
}

.clickable:hover {
  text-decoration: underline;
}

.footer {
  width: 100%;
  height: 35px;
  display: flex;
  flex-direction: row;
  justify-content: center;
}

.back {
  width: 100px;
  height: 100%;
  font-size: 20px;
}
</style>
