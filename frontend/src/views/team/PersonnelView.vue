<script setup lang="js">
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import { Back, InfoFilled, Plus, Minus } from "@element-plus/icons-vue";

// TODO: 建议提取函数到utils
const handleBack = () => {

}

// TODO: 用户是否团队的owner
const isOwner = true;

// TODO: 权限详情，弹出一个el-dialog窗口，窗口内容我来写
const authorityDetail = () => {

}

// TODO: 移除成员，弹出一个el-dialog窗口，窗口内容我来写
const handleRemoveMember = () => {

}

// TODO: 添加成员，弹出一个el-dialog窗口，窗口内容我来写
const handleAddMember = () => {

}
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <el-button
            link
            type="text"
            size="large"
            @click="handleBack"
        >
          <el-icon :size="25">
            <Back/>
          </el-icon>
        </el-button>
        <span class="route">
          <!--TODO: 第二级目录-->
          <span>&nbsp;>&nbsp;</span>
          <!--TODO: 第三级目录'xxx的团队空间'-->
          <span>&nbsp;>&nbsp;</span>
          <span class="present-directory">
            成员信息
          </span>
        </span>
      </div>
    </template>

    <div class="main-content-wrapper">
      <el-card class="box-card">
        <template #header>
          <div>
            <span v-if="isOwner" class="header">编辑</span>
            <span class="header">成员信息</span>
          </div>
        </template>

        <div class="main-content">
          <div class="key-container">
            <div class="key">
              拥有者
            </div>
            <el-button
                link
                type="text"
                class="info"
                @click="authorityDetail"
            >
              <el-icon>
                <InfoFilled/>
              </el-icon>
            </el-button>
          </div>
          <div class="value">
            TODO: 拥有者
          </div>
          <br>

          <div class="key-container">
            <div class="key">
              管理者
            </div>
            <el-button
                link
                type="text"
                class="info"
                @click="authorityDetail"
            >
              <el-icon>
                <InfoFilled/>
              </el-icon>
            </el-button>
            <el-button
                v-if="isOwner"
                class="authority-button"
            >
              <el-icon>
                <Minus/>
              </el-icon>
            </el-button>
            <el-button
                v-if="isOwner"
                class="authority-button"
            >
              <el-icon>
                <Plus/>
              </el-icon>
            </el-button>
          </div>
          <div class="value">
            TODO: 管理者
          </div>
          <br>

          <div class="key-container">
            <div class="key">
              参与者
            </div>
            <el-button
                link
                type="text"
                class="info"
                @click="authorityDetail"
            >
              <el-icon>
                <InfoFilled/>
              </el-icon>
            </el-button>
            <el-button
                v-if="isOwner"
                class="authority-button"
            >
              <el-icon>
                <Minus/>
              </el-icon>
            </el-button>
            <el-button
                v-if="isOwner"
                class="authority-button"
            >
              <el-icon>
                <Plus/>
              </el-icon>
            </el-button>
          </div>
          <div class="value">
            TODO: 参与者
          </div>
        </div>

        <template #footer>
          <div v-if="isOwner" class="footer">
            <el-button
                type="danger"
                class="remove-button"
                @click="handleRemoveMember"
            >
              移除成员
            </el-button>

            <el-button
                type="primary"
                class="add-button"
                @click="handleAddMember"
            >
              添加成员
            </el-button>
          </div>
          <div v-else class="footer">
            <el-button
                type="primary"
                class="back-button"
                @click="handleBack"
            >
              返回
            </el-button>
          </div>
        </template>
      </el-card>
    </div>
  </HeaderWrapper>
</template>

<style scoped>
.inner-header {
  left: 0;
  right: 0;
  top: 0;
  height: 100%;
  display: flex;
  flex-direction: row;
  gap: 15px;
  align-items: center;
}

.route {
  display: inline-flex;
  height: 100%;
  align-items: center;
  font-size: 20px;
  color: #333333;
}

.present-directory {
  font-weight: bold;
}

.main-content-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.box-card {
  width: 90%;
  height: 90%;
  display: flex;
  flex-direction: column;
}

.header {
  font-size: 25px;
  font-weight: bold;
}

:deep(.el-card__header) {
  border-bottom: none;
  display: flex;
  justify-content: center;
}

.main-content {
  margin-left: 25px;
  margin-right: 25px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.key-container {
  width: 100%;
  display: flex;
  flex-direction: row;
}

.key {
  font-weight: bold;
  font-size: 20px;
}

.info {
  margin-left: 5px;
  margin-right: 20px;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
  padding: 0;
}

.authority-button {
  padding: 5px;
  width: 40px;
  height: 40px;
}

.value {
  font-size: 18px;
}

.footer {
  width: 100%;
  height: 35px;
  display: flex;
  flex-direction: row;
  justify-content: center;
}

.remove-button {
  margin-left: 20%;
  margin-right: auto;
  width: 120px;
  height: 100%;
  font-size: 20px;
}

.add-button {
  margin-left: auto;
  margin-right: 20%;
  width: 120px;
  height: 100%;
  font-size: 20px;
}

.back-button {
  width: 100px;
  height: 100%;
  font-size: 20px;
}
</style>