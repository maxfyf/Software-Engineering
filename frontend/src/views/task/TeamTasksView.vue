<script setup lang="js">
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";
import { useRoute } from 'vue-router';
import { currentUser } from '@/store/user.js';

const route = useRoute();

// 只显示分配给当前用户的团队任务
const isVisibleTask = (task) => {
  if (!task.team) return false
  const assignee = task.assignee
  if (Array.isArray(assignee)) {
    return assignee.includes(currentUser.username)
  }
  return assignee === currentUser.username
}
</script>

<template>
  <TaskViewWrapper
      v-if="!route.path.includes('/detail') && !route.path.includes('/edit')"
      :filter-fn="isVisibleTask"
  />
  <router-view v-else />
</template>

<style scoped>

</style>