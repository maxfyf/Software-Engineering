<script setup lang="js">
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Route from "@/components/Route.vue";
import Search from "@/components/Search.vue";
import OperationList from "@/components/OperationList.vue";
import { useRoute, useRouter } from "vue-router";
import TaskList from "@/components/TaskList.vue";

const route = useRoute()
const router = useRouter()

// TODO: 搜索框数据集（操作对象）
const dataset = []

// TODO: 搜索框回调函数
const handleSelectObject = () => {

}

// TODO: operation类型数组
const operations = []

// TODO: 操作列表页面（可以类似TaskList做一个useOperationView.js）
const currentPage = 1;
const pageSize = 10;
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <div class="route-wrapper">
          <Route :route="route" :router="router" />
        </div>

        <div class="search-wrapper">
          <Search :dataset="dataset" :onSelect="handleSelectObject" />
        </div>
      </div>
    </template>

    <div class="main-content-wrapper">
      <OperationList
          :operations="operations"
          :current-page="currentPage"
          :page-size="pageSize"
      />
    </div>
  </HeaderWrapper>
</template>

<style scoped>
.route-wrapper {
  display: flex;
  left: 20px;
  align-items: center;
}

.search-wrapper {
  display: flex;
  position: absolute;
  right: 20px;
  width: 250px;
  align-items: center;
}

.main-content-wrapper {
  margin: 20px;
}
</style>