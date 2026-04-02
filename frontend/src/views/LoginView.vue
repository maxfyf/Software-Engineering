<script setup lang="js">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { handleLogin, handleRegister } from '@/store/user.js'


const router = useRouter()
const username = ref('')    //用户名
const password = ref('')    //登录密码
const first_time_password = ref('')    //注册密码
const repeated_password = ref('')    //确认密码
const first_name = ref('')    //名
const last_name = ref('')    //姓
const phone = ref('')    //电话号码
const email = ref('')    //电子邮箱

// 登录处理
const onHandleLogin = async () => {
  const result = await handleLogin({
    username: username.value,
    password: password.value
  })
  if (result && result.success && result.redirect) {
    router.replace(result.redirect)
  }
}

// 注册处理
const onHandleRegister = async () => {
  const result = await handleRegister({
    username: username.value,
    firstTimePassword: first_time_password.value,
    repeatedPassword: repeated_password.value,
    firstName: first_name.value,
    lastName: last_name.value,
    phone: phone.value,
    email: email.value
  })
  
  // 重置除了 username 以外的所有字段
  if (result && result.success) {
    if (result.redirect) router.push(result.redirect)
    if (result.resetFields) {
      username.value = result.resetFields.username
      first_time_password.value = result.resetFields.firstTimePassword
      repeated_password.value = result.resetFields.repeatedPassword
      first_name.value = result.resetFields.firstName
      last_name.value = result.resetFields.lastName
      phone.value = result.resetFields.phone
      email.value = result.resetFields.email
    }
  }
}
</script>

<script lang="js">
export default {
  data() {
    return {
      activeTab: 0,

      tabs: [
        {
          label: 'login',
          name: '登录'
        },
        {
          label: 'register',
          name: '注册'
        }
      ]
    };
  }
};
</script>

<template>
  <div class="page-container">
    <div class="box">
      <!-- 页面左侧为介绍文本与装饰图 -->
      <div class="left">
        <div class="introduction">
          <span class="title">协作式任务管理系统</span>
          <br>
          <span class="text">让您的团队工作更高效</span>
          <br>
        </div>
        <img
            src="/src/assets/images/login_page_decoration.png"
            class="decoration"
            alt="Decoration"
        >
      </div>

      <!-- 页面右侧为注册登录窗口 -->
      <div class="right">
        <div class="card">
          <!-- 顶部按钮 -->
          <el-button-group class="button-bar">
            <el-button
                v-for="(tab, index) in tabs"
                class="bar-button"
                :key="index"
                :type="activeTab === index ? 'primary' : 'default'"
                :class="activeTab === index ? 'bottom-border-only' : ''"
                @click="activeTab = index"
            >
              <span class="button-text">{{ tab.name }}</span>
            </el-button>
          </el-button-group>

          <!-- 下方登录/注册界面 -->
          <div class="content">
            <div v-if="activeTab === 0" class="inner-box">
              <el-input
                  class="input"
                  v-model="username"
                  type="text"
                  placeholder="用户名"
              />
              <el-input
                  class="input"
                  v-model="password"
                  type="password"
                  placeholder="密码"
                  show-password
              />
              <div class="spacer"/>
              <el-button
                  type="primary"
                  class="login-button"
                  @click="onHandleLogin"
              >
                <span class="login-button-text">登录</span>
              </el-button>
            </div>

            <div v-else class="inner-box">
              <div class="item">
                <span class="star">*&nbsp;</span>
                <el-input
                    class="input"
                    v-model="username"
                    type="text"
                    placeholder="用户名"
                />
              </div>
              <div class="item">
                <span class="star">*&nbsp;</span>
                <el-input
                    class="input"
                    v-model="first_time_password"
                    type="password"
                    placeholder="密码"
                    show-password
                />
              </div>
              <div class="item">
                <span class="star">*&nbsp;</span>
                <el-input
                    class="input"
                    v-model="repeated_password"
                    type="password"
                    placeholder="确认密码"
                    show-password
                />
              </div>
              <div class="item">
                <el-input
                    class="input-with-margin"
                    v-model="first_name"
                    type="text"
                    placeholder="名"
                />
              </div>
              <div class="item">
                <el-input
                    class="input-with-margin"
                    v-model="last_name"
                    type="text"
                    placeholder="姓"
                />
              </div>
              <div class="item">
                <el-input
                    class="input-with-margin"
                    v-model="phone"
                    type="tel"
                    placeholder="电话号码"
                />
              </div>
              <div class="item">
                <el-input
                    class="input-with-margin"
                    v-model="email"
                    type="email"
                    placeholder="电子邮箱"
                />
              </div>
              <div class="spacer"/>
              <el-button
                  type="primary"
                  class="login-button"
                  @click="onHandleRegister"
              >
                <span class="login-button-text">注册</span>
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  width: 100%;
  height: calc(100vh - 80px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.box {
  width: 1000px;
  height: 600px;
  display: flex;
  flex-direction: row;
  align-items: center;
}

.left {
  width: 400px;
  height: 100%;
  align-items: center;
  justify-content: center;
}

.introduction {
  color: black;
  text-align: center;
}

.title {
  font-size: 40px;
  font-weight: bold;
}

.text {
  font-size: 35px;
}

.decoration {
  margin-top: 20px;
  width: 395px;
  height: auto;
}

.right {
  width: 400px;
  height: 100%;
  margin-left: auto;
}

.card {
  width: 100%;
  height: 100%;
  border-radius: 10px;
  background-color: white;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.button-bar {
  top: 0;
  width: 100%;
  height: 60px;
  display: flex;
  flex-direction: row;
}

.bar-button {
  flex: 1;
  height: 100%;
  padding: 0;
  border-radius: 0;
  border: none;
  background-color: transparent;
}

.bar-button:hover {
  cursor: pointer;
  text-shadow: 2px 2px 3px rgba(0,0,0,0.5);
}

.el-button--primary.bottom-border-only {
  color: #409eff;
  border-bottom: 3px solid #409eff;
}

.button-text {
  display: inline-block;
  font-size: 20px;
  transition: all 0.3s;
}

.content {
  width: 100%;
  flex-grow: 1;
  display: flex;
}

.inner-box {
  margin: 40px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.item {
  width: 100%;
  display: flex;
  flex-direction: row;
}

.star {
  color: red;
}

.input :deep(.el-input__inner) {
  width: 100%;
  height: 35px;
  font-size: medium;
}

.input :deep(.el-icon) {
  color: #222222;
  cursor: pointer;
}

.input-with-margin {
  margin-left: 11px;
}

.input-with-margin :deep(.el-input__inner) {
  width: 100%;
  height: 35px;
  font-size: medium;
}

.input-with-margin :deep(.el-icon) {
  color: #222222;
  cursor: pointer;
}

.spacer {
  flex-grow: 1;
}

.login-button {
  width: 100%;
  height: 40px;
}

.login-button-text {
  font-size: 20px;
}
</style>
