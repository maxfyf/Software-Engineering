<script setup lang="js">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const isLoggedIn = ref(false)    //是否已登录
const route = useRoute()
const activeIndex = ref('/')    //当前网页路径

watch(() => route.path, (newPath) => {
  console.log('路径变化：', newPath)
  activeIndex.value = newPath
}, { immediate: true })

const handleSelect = (key) => {
  console.log('导航到:', key)
}

const handleLogin = () => {
  /*TODO: 登录
  * 1. 从后端加载用户信息与所有任务，存储到store/user.js
  * 2. 切换页面到/task页面
  * 3. 将isLoggedIn置为true */
}

const handleLogout = () => {
  /*TODO: 登出
  * 1. 删去store/user.js中的用户数据
  * 2. 将isLoggedIn置为false
  * 3. 切换页面到login页面 */
}
</script>

<template>
  <el-header class="navbar">
    <!-- 网站信息 -->
    <div class="site">
      <img src="/src/assets/images/logo.jpg" class="logo" alt="Logo">
      <span class="site-name">协作式任务管理系统</span>
    </div>

    <div v-if="isLoggedIn">
      <el-menu
          :default-active="activeIndex"
          mode="horizontal"
          router
          @select="handleSelect"
          class="main-menu"
      >
        <el-menu-item index="/task">📋 我的任务</el-menu-item>
        <el-menu-item index="/settings">⚙️ 设置</el-menu-item>
      </el-menu>
    </div>

    <!-- 账户信息 -->
    <div class="account">
      <div v-if="isLoggedIn">
        <span class="username">
          {{123/*TODO: 从store/user.js加载用户名*/}}
        </span>
        <el-button @click="handleLogout" type="danger" style="margin-right: 20px">
          登出
        </el-button>
      </div>

      <div v-else>
        <span class="info">
          未登录
        </span>
      </div>
    </div>
  </el-header>

  <main class="main">
    <router-view></router-view>
  </main>

  <footer class="footer">
    <p class="copyright">&copy; 2026 封逸凡、徐熙竣、丁泓森、赵冠杰、陈熙睿团队</p>
  </footer>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: white;
  height: 50px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-bottom: 1px solid #f0f0f0;
  z-index: 1000;
  transition: all 0.3s ease;
}

.site {
  display: flex;
  align-items: center;
}

.logo {
  margin-left: 15px;
  width: 40px;
  height: auto;
}

.site-name {
  margin-left: 15px;
  font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif;
  font-weight: 800;
  font-size: 30px;

  background: linear-gradient(135deg, #4ab7ff, #1e6ef0);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;

  text-shadow: 0 0 20px rgba(0, 160, 255, 0.3);

  display: inline-block;
}

.account {
  position: absolute;
  right: 0;
}

.username {
  font-size: medium;
  margin-right: 10px;
  color: black;
}

.info {
  font-size: large;
  margin-right: 20px;
  color: black;
}

.main {
  display: flex;
  color: white;
}

.footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 30px;
  background-color: #c0c0c0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.copyright {
  color: black;
  font-size: medium;
}

</style>
