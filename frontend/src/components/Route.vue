<script setup lang="js">
import { translate, handleBack } from "@/utils/routeManager.js"
import { Back } from "@element-plus/icons-vue";

const props = defineProps({
  route: {
    type: Object,
    required: true,
    default: ''
  },
  router: {
    type: Object,
    required: true,
    default: undefined
  }
})

const innerRoute = translate(props.route)
</script>

<template>
  <div class="inner-route">
    <el-button
        v-if="innerRoute.length > 1"
        link
        type="text"
        size="large"
        @click="handleBack(route, router, 1)"
    >
      <el-icon :size="25">
        <Back/>
      </el-icon>
    </el-button>

    <div class="gap"/>

    <div
        class="ancestor"
        v-for="(ancestor, index) in innerRoute.slice(0, innerRoute.length - 1)"
    >
      <span
          class="clickable"
          @click="handleBack(route, router, innerRoute.length - index - 1)"
      >
        {{ ancestor }}
      </span>
      <span>&nbsp;>&nbsp;</span>
    </div>

    <span class="present">
      {{ innerRoute[innerRoute.length - 1] }}
    </span>
  </div>
</template>

<style scoped>
.inner-route {
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
}

.gap {
  width: 10px;
}

.ancestor {
  display: inline-flex;
  height: 100%;
  align-items: center;
  font-size: 20px;
  color: #333333;
}

.clickable {
  cursor: pointer;
}

.clickable:hover {
  text-decoration: underline;
  color: #409eff;
}

.present {
  display: inline-flex;
  height: 100%;
  align-items: center;
  font-size: 20px;
  color: black;
  font-weight: bold;
}
</style>