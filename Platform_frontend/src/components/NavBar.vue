<template>
  <nav class="navbar">
    <div class="nav-container">
      <div class="nav-brand">
        <img src="../assets/monitor_logo.svg" alt="Logo" class="nav-logo" />
      </div>
      
      <div class="nav-links">
        <router-link 
          to="/voltage" 
          class="nav-link"
          :class="{ active: $route.path === '/voltage' }"
        >
          ⚡ Voltaje
        </router-link>
        <router-link 
          to="/current" 
          class="nav-link"
          :class="{ active: $route.path === '/current' }"
        >
          🔌 Corriente
        </router-link>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const $route = useRoute()
</script>

<style scoped>
.navbar {
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  padding: 1rem 0;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-logo {
  height: 32px;
  width: 200px;
}

.nav-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #495057;
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 200px;
}

.nav-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: #ffffff;
  color: #6c757d;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
  border: 1px solid #dee2e6;
  text-align: center;
}

.nav-link:hover {
  background: #e9ecef;
  color: #495057;
  border-color: #adb5bd;
}

.nav-link.active {
  background: #495057;
  color: white;
  border-color: #495057;
}

@media (max-width: 768px) {
  .nav-container {
    padding: 0 0.5rem;
  }
  
  .nav-links {
    max-width: 180px;
  }
  
  .nav-link {
    padding: 10px 12px;
    font-size: 0.9rem;
  }
}
</style>
