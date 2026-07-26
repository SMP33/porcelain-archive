<script setup>
import AppHeader from './AppHeader.vue'
</script>

<template>
  <div class="ceramic-reset tw:bg-white tw:text-ink-800 tw:font-sans tw:min-h-screen tw:flex tw:flex-col">
    <AppHeader />
    <router-view />
  </div>
</template>
