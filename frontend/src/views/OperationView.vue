<script setup lang="js">
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Route from "@/components/Route.vue";
import Search from "@/components/Search.vue";
import OperationList from "@/components/OperationList.vue";
import { useRoute, useRouter } from "vue-router";
import { useOperationView } from "@/utils/useOperationView.js";

const route = useRoute()
const router = useRouter()

const {
  dataset,
  operations,
  currentPage,
  pageSize,
  handleSelectObject,
  handleSearchObject,
  handlePageChange
} = useOperationView()
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <div class="route-wrapper">
          <Route :route="route" :router="router" />
        </div>

        <div class="search-wrapper">
          <Search
              :dataset="dataset"
              :onSelect="handleSelectObject"
              :showAux="true"
              @search="handleSearchObject"
          />
        </div>
      </div>
    </template>

    <div class="main-content-wrapper">
      <div class="header-spacer"/>
      <OperationList
          :route="route"
          :operations="operations"
          :current-page="currentPage"
          :page-size="pageSize"
          @page-change="handlePageChange"
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

.header-spacer {
  width: 100%;
  height: 30px;
}

:deep(.el-pagination .el-pager li) {
  background-color: transparent !important;
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next) {
  background-color: transparent !important;
  color: black !important;
}
</style>