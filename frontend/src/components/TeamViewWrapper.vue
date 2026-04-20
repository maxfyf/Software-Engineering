<script setup lang="js">
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Search from "@/components/Search.vue";
import TeamList from "@/components/TeamList.vue";
import { useTeamView } from "@/utils/useTeamView.js";
import { Plus } from "@element-plus/icons-vue";

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  filterFn: {
    type: Function,
    default: null
  },
  showNewButton: {
    type: Boolean,
    default: false
  }
})

const {
  teams,
  dataset,
  router,
  createDialogVisible,
  newTeamTitle,
  handleSelect,
  handleNew,
  handleCreateTeam,
  handleCancelCreate,
  handleEnterTeamSpace
} = useTeamView(props.filterFn, props.title)
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <span class="route">{{ title }}</span>
        <div class="search-wrapper">
          <Search :data="dataset" :onSelect="handleSelect" />
        </div>
      </div>
    </template>

    <div class="main-content-wrapper">
      <div v-if="showNewButton" class="header">
        <el-button type="primary" class="new-button" @click="handleNew">
          <el-icon><Plus/></el-icon>
          &nbsp;新建团队
        </el-button>
      </div>

      <TeamList
          :teams="teams"
          :router="router"
          @enter-team-space="handleEnterTeamSpace"
      />
    </div>

    <!-- 新建团队弹窗 -->
    <el-dialog
        v-model="createDialogVisible"
        title="新建团队"
        width="400px"
    >
      <el-form label-width="80px">
        <el-form-item label="团队名称">
          <el-input v-model="newTeamTitle" placeholder="请输入团队名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="handleCancelCreate">取消</el-button>
        <el-button type="primary" @click="handleCreateTeam">确定</el-button>
      </template>
    </el-dialog>
  </HeaderWrapper>
</template>

<style scoped>
.inner-header {
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
}

.route {
  display: inline-flex;
  height: 100%;
  align-items: center;
  font-size: 20px;
  font-weight: bold;
  color: #333333;
}

.search-wrapper {
  display: flex;
  position: absolute;
  right: 20px;
  width: 250px;
  align-items: center;
}

.main-content-wrapper {
  margin-top: 20px;
  margin-left: 20px;
  margin-right: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.header {
  width: 100%;
  display: flex;
}

.new-button {
  width: 100px;
  margin-left: auto;
  margin-right: 15px;
}
</style>