<template><router-view /></template>
<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
const auth = useAuthStore()
onMounted(() => auth.fetchUser())
</script>
<style>
body { margin: 0; font-family: 'PingFang SC','Microsoft YaHei',sans-serif; background: #f0f2f5; }
</style>
