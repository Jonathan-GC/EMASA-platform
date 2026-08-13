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
        <TableAudit ref="tableAuditRef" />
      </div>
    </ion-content>
  </ion-page>
</template>

<script setup>
import { ref, inject } from 'vue'
import { onIonViewWillEnter } from '@ionic/vue'
import TableAudit from '@components/tables/audit/TableAudit.vue'

const icons = inject('icons', {})

const tableAuditRef = ref(null)

onIonViewWillEnter(() => {
  tableAuditRef.value?.fetchLogs(true)
})
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
