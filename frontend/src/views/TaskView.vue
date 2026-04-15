<script setup lang="js">
import SidebarWrapper from "@/components/SidebarWrapper.vue";
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from "vue-router";

const route = useRoute()
const router = useRouter()

// 记录先前的路由路径，用于编辑任务后返回
const previousRoute = ref('/task/all')

// 监听路由变化，记录非编辑页面的路径
watch(() => route.path, (newPath) => {
  if (!newPath.startsWith('/task/edit')) {
    previousRoute.value = newPath
  }
}, { immediate: true })

const activeMenu = computed(() => {
  if (route.path.startsWith('/task/all')) {
    return '/task/all'
  }
  else if (route.path.startsWith('/task/edit')) {
    // 返回先前记录的路由路径
    return previousRoute.value
  }
  else
    return route.path
})
const activeIndex = ref('/task/')

watch(() => route.path, (newPath) => {
  activeIndex.value = newPath
}, { immediate: true })

const goBack = () => {
  router.push(previousRoute.value)
}
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
        <el-menu-item index="/task/all" class="secondary-route">
          全部任务
        </el-menu-item>

        <el-menu-item index="/task/personal" class="secondary-route">
          个人任务
        </el-menu-item>

        <el-menu-item index="/task/team" class="secondary-route">
          团队任务
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