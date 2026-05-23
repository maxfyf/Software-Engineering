<script setup lang="js">
import { computed, ref, onMounted, nextTick } from "vue";
import { translate, handleBack } from "@/utils/routeManager.js"
import { Back, MoreFilled } from "@element-plus/icons-vue";
import { contentWidth } from "@/store/layout.js";

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
  },
  width: {
    type: Number,
    default: undefined
  }
})

const innerRoute = translate(props.route)
const collapse = ref(false)
const routeWidths = ref([])
const separatorWidth = ref(undefined)
const prefixWidth = ref(35)
const iconWidth = ref(25)
const maxWidth = computed(() => props.width === undefined ? (contentWidth.value - 200) : props.width)
const invisibleRoute = ref([]);
const visibleRoute = ref([]);

// 计算可见的路由
const computeVisibleRoute = async () => {
  await nextTick()
  visibleRoute.value = [...innerRoute]
  if(innerRoute.length <= 1) return false

  const tempDiv = document.createElement('div')
  tempDiv.style.position = 'absolute'
  tempDiv.style.visibility = 'hidden'
  tempDiv.style.whiteSpace = 'nowrap'
  tempDiv.style.fontSize = '20px'
  tempDiv.style.height = 'auto'
  tempDiv.style.top = '-9999px'
  document.body.appendChild(tempDiv)

  for (let i = 0; i < innerRoute.length; i++) {
    const span = document.createElement('span')
    span.innerText = innerRoute[i]
    span.style.display = 'inline-flex'
    if (i === innerRoute.length - 1) {
      span.style.fontWeight = 'bold'
    }
    tempDiv.appendChild(span)
    const textWidth = span.offsetWidth
    tempDiv.removeChild(span)
    routeWidths.value.push(textWidth)
  }

  const sep = document.createElement('span')
  sep.innerText = ' > '
  sep.style.display = 'inline-block'
  sep.style.margin = '0 4px'
  tempDiv.appendChild(sep)
  separatorWidth.value = sep.offsetWidth
  tempDiv.removeChild(sep)

  let sum = routeWidths.value.reduce((acc, cur) => acc + cur, 0)
  sum = sum + prefixWidth.value + (innerRoute.length - 1) * separatorWidth.value
  if(sum <= maxWidth.value)
    return false

  invisibleRoute.value.push(innerRoute[0])
  visibleRoute.value = [...innerRoute.slice(1)]
  sum = sum - routeWidths.value[0] + iconWidth.value

  let cnt = 1
  while(visibleRoute.value.length > 1 && sum > maxWidth.value) {
    invisibleRoute.value.push(innerRoute[cnt])
    visibleRoute.value = [...innerRoute.slice(cnt + 1)]
    sum = sum - routeWidths.value[cnt] - separatorWidth.value
    cnt = cnt + 1
  }
  return true
}

onMounted(async () => {
  collapse.value = await computeVisibleRoute()
})

const handleCommand = (index) => {
  handleBack(props.route, props.router, innerRoute.length - index - 1)
}
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

    <div v-if="collapse" class="inner-route">
      <el-dropdown trigger="click" @command="handleCommand">
        <el-icon :size="25">
          <MoreFilled/>
        </el-icon>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item
                v-for="(item, index) in invisibleRoute"
                :key="index"
                :command="index"
            >
              <span>{{ item }}</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <span class="ancestor">&nbsp;>&nbsp;</span>

      <div
          class="ancestor"
          v-for="(ancestor, index) in visibleRoute.slice(0, visibleRoute.length - 1)"
      >
        <span
            class="clickable"
            @click="handleBack(route, router, visibleRoute.length - index - 1)"
        >
          {{ ancestor }}
        </span>
        <span>&nbsp;>&nbsp;</span>
      </div>
    </div>
    <div
        v-else
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

.present {
  display: inline-flex;
  height: 100%;
  align-items: center;
  font-size: 20px;
  color: black;
  font-weight: bold;
}
</style>