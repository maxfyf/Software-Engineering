<script setup lang="js">
import HeaderWrapper from "@/components/HeaderWrapper.vue";
import Search from "@/components/Search.vue"

// TODO: 改成实际用户所有任务名称字符串数组
const dataset = ['apple', 'banana', 'pear', 'peach']

// TODO: 改成实际选中选项后的回调函数（切换页面到指定任务对应的页面）
const handleSelect = () => {}

</script>

<template>
  <HeaderWrapper>
    <template #header>
      <div class="inner-header">
        <span class="route">全部任务</span>
        <div class="search-wrapper">
          <Search
              :data="dataset"
              :onSelect="handleSelect"
          />
        </div>
      </div>
    </template>

    <div>

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

.search-wrapper {
  display: flex;
  position: absolute;
  right: 20px;
  width: 250px;
  align-items: center;
}
</style>