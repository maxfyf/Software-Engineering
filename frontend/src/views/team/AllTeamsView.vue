<script setup lang="js">
import TeamViewWrapper from "@/components/TeamViewWrapper.vue";
import { useRoute } from 'vue-router';

const route = useRoute();
</script>

<template>
  <TeamViewWrapper
      v-if="!route.path.includes('/space')"
      title="全部团队"
      :show-new-button="true"
  />
  <router-view v-else />
</template>

<style scoped>

</style>