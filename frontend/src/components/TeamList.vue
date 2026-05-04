<script setup lang="js">
import { currentUser, highlightTeamId, removeTeam} from "@/store/user.js";
import { ElMessage, ElMessageBox } from "element-plus";
import TwoColumnsWrapper from "@/components/TwoColumnsWrapper.vue";
import { Delete, Right } from "@element-plus/icons-vue";

const props = defineProps({
  teams: {
    type: Array,
    required: true,
    default: () => []
  }
})

const emit = defineEmits(['enterTeamSpace'])

// 判定用户角色
const role = (item) => {
  const username = currentUser.username;
  if (username === item.owner)
    return '拥有者'
  else if (item.admin.includes(username))
    return '管理者'
  else if (item.member.includes(username))
    return '参与者'
  else {
    ElMessage.error('非法访问团队')
    return null
  }
}

// 解散团队
const deleteTeam = (item) => {
  ElMessageBox.confirm(
      `确定要解散团队"${item.title}"吗？`,
      '',
      {
        confirmButtonText: '确定',
        confirmButtonType: 'danger',
        cancelButtonText: '取消',
        type: undefined
      }
  ).then(() => {
    highlightTeamId.value = null
    removeTeam(item.id)
    ElMessage.success('团队已解散')
  }).catch(() => {
    console.log('取消删除')
  })
}

// 进入团队空间
const enterTeamSpace = (item) => {
  console.log('进入团队空间:', item.id)
  highlightTeamId.value = item.id
  emit('enterTeamSpace', item.id)
}
</script>

<template>
  <TwoColumnsWrapper :items="props.teams" empty-text="暂无团队">
    <template #item="{ item }">
      <el-card :class="item.id === highlightTeamId ? 'highlight-card' : 'card' ">
        <div class="card-content">
          <div class="title-line">
            <span class="title">{{item.title}}</span>
            <el-button
                link
                type="text"
                class="delete-button"
                v-if="item.owner === currentUser.username"
                @click="deleteTeam(item)"
            >
              <el-icon>
                <Delete/>
              </el-icon>
            </el-button>
          </div>

          <div class="info-line">
            <div class="info-wrapper">
            <span class="info">
              创建者：{{item.owner}}
            </span>
              <span class="info">
              成员：{{1 + item.admin.length + item.member.length}}人
            </span>
              <span class="info">
              我的角色：{{role(item)}}
            </span>
            </div>
            <el-button
                link
                type="text"
                class="enter-button"
                @click="enterTeamSpace(item)"
            >
              <el-icon>
                <Right/>
              </el-icon>
            </el-button>
          </div>
        </div>
      </el-card>
    </template>
  </TwoColumnsWrapper>
</template>

<style scoped>
.card {
  background-color: white;
  height: 100% !important;
  display: flex;
  flex-direction: column;
}

.highlight-card {
  background-color: #ecf5ff;
  border-color: #ecf5ff;
  height: 100% !important;
  display: flex;
  flex-direction: column;
}

.card-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content:space-between;
  gap: 20px;
}

.title-line {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.title {
  font-size: 25px;
  font-weight: bold;
}

.delete-button {
  font-size: 20px;
  margin-left: auto;
  margin-right: 0;
}

.delete-button:hover {
  color: #f56c6c !important;
}

.info-line {
  display: flex;
  flex-direction: row;
  align-items: center;
}

.info-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 0 30px;
  margin-right: 20px;
}

.info {
  display: inline-block;
  width: auto;
}

.enter-button {
  font-size: 30px;
  margin-left: auto;
  margin-right: 0;
}
</style>