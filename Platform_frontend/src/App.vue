<script setup lang="ts">
import NavBar from './components/NavBar.vue'
</script>

<template>
  <div id="app">
    <NavBar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f9fafb;
  min-height: 100vh;
  min-width: 100%;
  margin: 0;
  padding: 0;
  display:flex
}

.main-content {
  padding: 0 20px 20px;
  width: 100%;
  margin: 0 auto;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
}

@media (max-width: 768px) {
  .main-content {
    padding: 0 10px 20px;
  }
}
</style>