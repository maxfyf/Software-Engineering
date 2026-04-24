<script setup lang="js">
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";
import { useRoute } from 'vue-router';

const route = useRoute();
const isPersonalTask = (task) => !task.team
</script>

<template>
  <TaskViewWrapper
      v-if="!route.path.includes('/edit')"
      title="个人任务"
      :filter-fn="isPersonalTask"
      :show-new-button="true"
  />
  <router-view v-else />
</template>

<style scoped>

</style>