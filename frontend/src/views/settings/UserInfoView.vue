<script setup lang="js">
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import { handleCancelAccount } from "@/store/user.js";
</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <span class="route">个人资料</span>
      </div>
    </template>

    <div class="main-content-wrapper">
      <el-card class="box-card">
        <p class="item"><span class="key">用户名：</span>TODO</p>
        <p class="item"><span class="key">名：</span>TODO</p>
        <p class="item"><span class="key">姓：</span>TODO</p>
        <p class="item"><span class="key">电话号码：</span>TODO</p>
        <p class="item"><span class="key">电子邮箱：</span>TODO</p>

        <template #footer>
          <div class="footer">
            <el-button
                class="cancel-button"
                type="danger"
                @click="handleCancelAccount"
            >
              注销账号
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

.main-content-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.box-card {
  width: 95%;
  height: 95%;
  display: flex;
  flex-direction: column;
}

.item {
  width: 100%;
  display: flex;
  align-items: center;
  margin-top: 20px;
  font-size: 20px;
}

.key {
  font-weight: bold;
}

.footer {
  width: 100%;
  height: 35px;
  display: flex;
  justify-content: center;
}

.cancel-button {
  width: 100px;
  height: 100%;
  font-size: 20px;
}
</style>