<script setup>
import { computed } from 'vue';

const props = defineProps({
  items: {
    type: Array,
    required: true,
    default: () => []
  },
  emptyText: {
    type: String,
    default: ''
  }
});

const rowList = computed(() => {
  const rows = [];
  for (let i = 0; i < props.items.length; i += 2) {
    rows.push(props.items.slice(i, i + 2));
  }
  return rows;
});
</script>

<template>
  <div v-if="items.length === 0" class="empty-text-container">
    <span class="empty-text">
      {{ emptyText }}
    </span>
  </div>
  <div v-else class="two-column-container">
    <div class="column">
      <div v-for="(row, rowIndex) in rowList" class="row">
        <div v-for="(item, columnIndex) in row" class="item-wrapper">
          <slot name="item" :item="item" :index="2 * rowIndex + columnIndex" />
        </div>
        <div v-if="row.length === 1" class="item-wrapper"/>
      </div>
    </div>
  </div>
</template>

<style scoped>
.empty-text-container {
  width: 100%;
  margin-top: 3%;
  display: flex;
  justify-content: center;
}

.empty-text {
  font-size: 18px;
  color: dimgrey;
}

.two-column-container {
  margin-top: 5px;
  margin-bottom: 20px;
  gap: 20px;
}

.column {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.row {
  display: flex;
  flex-direction: row;
  gap: 15px;
}

.item-wrapper {
  flex: 1;
  top: 0;
  bottom: 0;
}
</style>