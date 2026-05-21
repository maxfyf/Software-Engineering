<script setup lang="js">
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";
import { useRoute } from 'vue-router';
import { currentUser } from '@/store/user.js';

const route = useRoute();

// 个人任务 + 分配给当前用户的团队任务
const isVisibleTask = (task) => {
  // 个人任务：自己创建的
  if (!task.team && task.owner === currentUser.username) {
    return true
  }
  // 团队任务：只有负责人可见
  if (task.team) {
    const assignee = task.assignee
    if (Array.isArray(assignee)) {
      return assignee.includes(currentUser.username)
    }
    return assignee === currentUser.username
  }
  return false
}
</script>

<template>
  <TaskViewWrapper
      v-if="!route.path.includes('/detail') && !route.path.includes('/edit')"
      :filter-fn="isVisibleTask"
      :show-new-button="true"
  />
  <router-view v-else />
</template>

<style scoped>

</style>