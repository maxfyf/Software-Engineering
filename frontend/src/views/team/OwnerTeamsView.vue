<script setup lang="js">
import TeamViewWrapper from "@/components/TeamViewWrapper.vue";
import { currentUser } from "@/store/user.js";

const isOwner = (team) => team.owner === currentUser.username
</script>

<template>
  <TeamViewWrapper
      title="我拥有的团队"
      :filter-fn="isOwner"
      :show-new-button="true"
  />
</template>

<style scoped>

</style>