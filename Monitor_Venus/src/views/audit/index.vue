<template>
  <ion-page>
    <ion-content :fullscreen="true">
      <div class="current-dashboard">
        <div class="header">
          <div class="header-title">
            <ion-back-button default-href="/home"></ion-back-button>
            <h1>
              <ion-icon :icon="icons.time"></ion-icon>
              Auditoría
            </h1>
          </div>
        </div>
        <TableAudit />
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { inject } from 'vue'
import TableAudit from '@components/tables/audit/TableAudit.vue'

const icons = inject('icons', {})
</script>

<style scoped>
@import '@assets/css/dashboard.css';

.header {
  margin-bottom: 30px;
}

@media (max-width: 768px) {
  .header h1 {
    font-size: 1.5rem;
  }
}
</style>
