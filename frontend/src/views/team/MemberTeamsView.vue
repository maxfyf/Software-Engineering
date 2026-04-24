<script setup lang="js">
import TeamViewWrapper from "@/components/TeamViewWrapper.vue";
import { currentUser } from "@/store/user.js";
import { useRoute } from 'vue-router';

const route = useRoute();
const isMember = (team) => team.member.includes(currentUser.username)
</script>

<template>
  <TeamViewWrapper
      v-if="!route.path.includes('/space')"
      title="我参与的团队"
      :filter-fn="isMember"
      :show-new-button="false"
  />
  <router-view v-else />
</template>

<style scoped>

</style>