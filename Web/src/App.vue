<template>
  <playground msg="Welcome to playground"/>
</template>

<script setup lang="ts">
import playground from './components/playground.vue'
import {useDark, useToggle} from '@vueuse/core'

// 夜间暗色模式
// const isDark = useDark()
// const toggleDark = useToggle(isDark)

</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f8fa;
}

body {
  margin: 0;
  padding: 0;
  background-color: #f5f8fa;
}
</style>
