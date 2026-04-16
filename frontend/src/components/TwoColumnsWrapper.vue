<script setup>
import { computed } from 'vue';

const props = defineProps({
  items: {
    type: Array,
    required: true,
    default: () => []
  }
});

// 拆分奇偶索引
const leftList = computed(() => props.items.filter((_, index) => index % 2 === 0));
const rightList = computed(() => props.items.filter((_, index) => index % 2 !== 0));
</script>

<template>
  <div class="two-column-container">
    <!-- 左侧列 -->
    <div class="column">
      <template v-for="(item, index) in leftList" :key="2 * index">
        <slot name="item" class="item-container" :item="item" :index="2 * index"/>
      </template>
    </div>

    <!-- 右侧列 -->
    <div class="column">
      <template v-for="(item, index) in rightList" :key="2 * index + 1">
        <slot name="item" class="item-container" :item="item" :index="2 * index + 1"/>
      </template>
    </div>
  </div>
</template>

<style scoped>
.two-column-container {
  display: flex;
  margin-top: 5px;
  margin-bottom: 20px;
  gap: 20px;
}

.column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}
</style>