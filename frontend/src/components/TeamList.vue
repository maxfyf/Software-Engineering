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
  },

  router: {
    type: Object,
    required: true
  }
})

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
const deleteTeam = (item, index) => {
  highlightTeamId.value = null
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
    removeTeam(index)
    ElMessage.success('团队已解散')
  }).catch(() => {
    console.log('取消删除')
  })
}

// 进入团队空间
const enterTeamSpace = (index) => {
  console.log('进入团队空间:', index)
  highlightTeamId.value = index
  props.router.push({
    path: '/team/space',
    query: {
      isNew: 'false',
      team: index
    }
  })
}
</script>

<template>
  <TwoColumnsWrapper :items="props.teams">
    <template #item="{ item, index }">
      <el-card :class="index === highlightTeamId ? 'highlight-card' : 'card' ">
        <div class="line">
          <span class="title">{{item.title}}</span>
          <el-button
              link
              type="text"
              class="delete-button"
              v-if="item.owner === currentUser.username"
              @click="deleteTeam(item, index)"
          >
            <el-icon>
              <Delete/>
            </el-icon>
          </el-button>
        </div>

        <br>

        <div class="line">
          <span class="info">
            创建者：{{item.owner}}&nbsp;&nbsp;&nbsp;
            成员：{{1 + item.admin.length + item.member.length}}人&nbsp;&nbsp;&nbsp;
            我的角色：{{role(item)}}
          </span>
          <el-button
              link
              type="text"
              class="enter-button"
              @click="enterTeamSpace(index)"
          >
            <el-icon>
              <Right/>
            </el-icon>
          </el-button>
        </div>
      </el-card>
    </template>
  </TwoColumnsWrapper>
</template>

<style scoped>
.card {
  background-color: white;
  display: flex;
  flex-direction: column;
}

.highlight-card {
  background-color: #d9ecff;
  border-color: #d9ecff;
  display: flex;
  flex-direction: column;
}

.line {
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

.enter-button {
  font-size: 30px;
  margin-left: auto;
  margin-right: 0;
}
</style>