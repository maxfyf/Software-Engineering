<script setup lang="js">
import TeamViewWrapper from "@/components/TeamViewWrapper.vue";
import { currentUser } from "@/store/user.js";

const isMember = (team) => team.member.includes(currentUser.username)
</script>

<template>
  <TeamViewWrapper
      title="我参与的团队"
      :filter-fn="isMember"
      :show-new-button="false"
  />
</template>

<style scoped>

</style>