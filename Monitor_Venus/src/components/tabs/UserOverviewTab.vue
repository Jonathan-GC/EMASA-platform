<template>
  <div class="content-card">
    <h3 class="content-card-title">
      <ion-icon :icon="icons.time"></ion-icon>
      Línea de Actividad
    </h3>
    <div class="activity-placeholder">
      <ion-icon :icon="icons.time" size="large" color="medium"></ion-icon>
      <p>No hay actividad reciente para mostrar.</p>
      <span class="placeholder-hint">Los registros de auditoría aparecerán aquí.</span>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue'

const icons = inject('icons', {})
</script>

<style scoped>
.content-card {
  box-sizing: border-box;
  width: 100%;
  background: var(--ion-card-background, #fff);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.content-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 20px 0;
  color: var(--ion-text-color);
}

.activity-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 20px;
  text-align: center;
  color: var(--ion-color-medium);
}

.activity-placeholder p {
  margin: 0;
  font-size: 0.95rem;
}

.placeholder-hint {
  font-size: 0.8rem;
  opacity: 0.7;
}

@media (max-width: 768px) {
  .content-card {
    padding: 16px;
  }
}
</style>
