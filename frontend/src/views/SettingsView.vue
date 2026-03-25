<script setup lang="js">
import SidebarWrapper from "@/components/SidebarWrapper.vue";
import { computed, ref, watch } from 'vue';
import { useRoute } from "vue-router";

const route = useRoute()
const activeMenu = computed(() => {
  if (route.path.startsWith('/settings/info')) {
    return '/settings/info'
  }
  else
    return route.path
})
const activeIndex = ref('/settings')    //当前网页路径

watch(() => route.path, (newPath) => {
  activeIndex.value = newPath
}, { immediate: true })
</script>

<template>
  <SidebarWrapper>
    <template #sidebar>
      <el-menu
          mode="vertical"
          :default-active="activeMenu"
          class="sidebar-menu"
          :router="true"
      >
        <el-menu-item index="/settings/info" class="secondary-route">
          个人资料
        </el-menu-item>
      </el-menu>
    </template>

    <router-view/>
  </SidebarWrapper>
</template>

<style scoped>
.sidebar-menu {
  width: 100%;
  flex-grow: 1;
  border: transparent;
}

.secondary-route {
  width: 100%;
  height: 45px;
  border-style: solid;
  border-width: thin;
  border-color: lightgray;
  border-top: transparent;
  border-left: transparent;
  border-right: transparent;
  font-size: large;
  cursor: pointer;
}

.secondary-route:hover {
  color: #409eff;
  text-shadow: 2px 2px 3px rgba(0,0,0,0.5);
}
</style>