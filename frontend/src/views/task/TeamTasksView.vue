<script setup lang="js">
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";
import { useRoute } from 'vue-router';

const route = useRoute();
const isTeamTask = (task) => task.team
</script>

<template>
  <TaskViewWrapper
      v-if="!route.path.includes('/edit')"
      title="团队任务"
      :filter-fn="isTeamTask"
  />
  <router-view v-else />
</template>

<style scoped>

</style>