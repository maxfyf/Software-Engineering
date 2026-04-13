<script setup lang="js">

</script>

<!-- 含顶栏的界面 -->
<template>
  <div class="page-with-header">
    <!-- 顶栏 -->
    <el-header class="header">
      <div class="header-content">
        <slot name="header"/>
      </div>
    </el-header>

    <!-- 内容区 -->
    <main class="content">
      <slot/>
    </main>
  </div>
</template>

<style scoped>
.page-with-header {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.header {
  top: 0;
  width: 100%;
  height: 50px;
  background-color: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-style: solid;
  border-width: thin;
  border-color: lightgray;
  border-top: transparent;
  border-left: transparent;
  border-right: transparent;
}

.header-content {
  margin-left: 20px;
  margin-right: 20px;
  height: 100%;
}

.content {
  flex: 1;
  overflow: auto;
}
</style>