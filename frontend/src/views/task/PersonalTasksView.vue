<script setup lang="js">
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";
import { useRoute } from 'vue-router';
import { currentUser } from '@/store/user.js';

const route = useRoute();
const isPersonalTask = (task) => {
  if (!task.team) return true
  const assignee = task.assignee
  if (Array.isArray(assignee)) {
    return assignee.includes(currentUser.username)
  }
  return assignee === currentUser.username
}
</script>

<template>
  <TaskViewWrapper
      v-if="!route.path.includes('/edit')"
      :filter-fn="isPersonalTask"
      :show-new-button="true"
  />
  <router-view v-else />
</template>

<style scoped>

</style>