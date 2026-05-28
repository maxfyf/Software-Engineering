<script setup lang="js">
import TaskViewWrapper from "@/components/TaskViewWrapper.vue";
import { useRoute } from 'vue-router';

const route = useRoute();
const isPersonalTask = (task) => {
  return !task.team
}
</script>

<template>
  <TaskViewWrapper
      v-if="!route.path.includes('/detail') && !route.path.includes('/edit')"
      :filter-fn="isPersonalTask"
      :show-new-button="true"
  />
  <router-view v-else />
</template>

<style scoped>

</style>