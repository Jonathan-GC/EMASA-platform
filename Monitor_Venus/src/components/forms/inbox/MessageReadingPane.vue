<template>
  <div class="reading-pane">
    <div v-if="!selectedMessage" class="no-selection">
      <ion-icon :icon="icons.mailOpen || icons.mail" class="placeholder-icon" />
      <p>Seleccione un mensaje para leerlo</p>
    </div>
    <div v-else class="reading-content">
      <div class="reading-header">
        <h2 class="reading-subject">{{ selectedMessage.subject }}</h2>
        <div class="reading-actions">
          <ion-badge v-if="selectedMessage.unread" color="primary">Unread</ion-badge>
          
          <!-- Assignment button -->
          <ion-button 
            v-if="isSupportManager" 
            :id="isMobile ? 'assign-trigger-mobile' : 'assign-trigger'" 
            size="small" 
            fill="outline"
            @click="$emit('openAssignPopover', $event)" 
            :disabled="membersLoading || assigning"
          >
            <ion-icon :icon="icons.personAdd || icons.person" :slot="isMobile ? 'icon-only' : 'start'" />
            <span v-if="!isMobile && assigneeId">Cambiar asignado</span>
            <span v-if="!isMobile && !assigneeId">Asignar a</span>
          </ion-button>
          <ion-spinner v-if="isSupportManager && (membersLoading || assigning)" name="dots" />
          
          <!-- Priority button -->
          <ion-button 
            v-if="isSupportManager" 
            :id="isMobile ? 'priority-trigger-mobile' : 'priority-trigger'" 
            size="small" 
            fill="outline"
            @click="$emit('openPriorityPopover', $event)" 
            :disabled="!selectedMessage || updatingPriority"
          >
            <ion-icon :icon="icons.flag || icons.alert" :slot="isMobile ? 'icon-only' : 'start'" />
            <span v-if="!isMobile">Cambiar prioridad</span>
          </ion-button>
          <ion-spinner v-if="isSupportManager && updatingPriority" name="dots" />
        </div>
      </div>
      
      <div class="reading-meta">
        <span class="from">{{ isMobile ? 'From' : 'De' }}: <strong>{{ selectedMessage.from }}</strong></span>
        <span v-if="selectedMessage.email" class="email">{{ isMobile ? 'Email' : 'Correo electrónico' }}: <strong>{{ selectedMessage.email }}</strong></span>
        <span class="org">{{ isMobile ? 'Organization' : 'Organización' }}: <strong>{{ selectedMessage.organization }}</strong></span>
        <span class="prio">{{ isMobile ? 'Priority' : 'Prioridad' }}: <ion-badge :color="priorityColor(selectedMessage.priority)">{{ selectedMessage.priority }}</ion-badge></span>
        <span class="date">{{ formatDate(selectedMessage.date) }}</span>
      </div>
      
      <div v-if="assigneeId" class="assigned-line">
        {{ isMobile ? 'Assigned' : 'Asignado' }}: <strong>{{ resolveAssigneeName(assigneeId) }}</strong>
      </div>
      
      <div class="assign-feedback">
        <span v-if="membersError" class="error-line">{{ membersError }}</span>
        <span v-if="assignError" class="error-line">{{ assignError }}</span>
        <span v-if="assignSuccess" class="success-line">{{ assignSuccess }}</span>
        <span v-if="priorityError" class="error-line">{{ priorityError }}</span>
        <span v-if="prioritySuccess" class="success-line">{{ prioritySuccess }}</span>
      </div>
      
      <div class="detail-grid">
        <div v-if="selectedMessage.category"><label>Categoría</label><span>{{ selectedMessage.category }}</span></div>
        <div v-if="selectedMessage.infrastructure_category"><label>Infraestructura</label><span>{{ selectedMessage.infrastructure_category }}</span></div>
        <div v-if="selectedMessage.machine_type"><label>Máquina</label><span>{{ selectedMessage.machine_type }}</span></div>
        <div v-if="selectedMessage.electric_machine_subtype"><label>Eléctrico</label><span>{{ selectedMessage.electric_machine_subtype }}</span></div>
        <div v-if="selectedMessage.mechanical_machine_subtype"><label>Mecánico</label><span>{{ selectedMessage.mechanical_machine_subtype }}</span></div>
      </div>
      
      <pre class="reading-body">{{ selectedMessage.body }}</pre>
      
      <!-- Attachments section -->
      <div class="attachments" v-if="attachmentsLoading || attachmentsError || attachments.length">
        <div class="attachments-title">
          <ion-icon :icon="icons.attach || icons.document" class="attach-icon" />
          <span>Adjuntos</span>
        </div>
        <div v-if="attachmentsLoading" class="attachments-loading">
          <ion-spinner name="dots" />
          <span>Cargando adjuntos...</span>
        </div>
        <div v-else-if="attachmentsError" class="error-line">{{ attachmentsError }}</div>
        <ul v-else class="attachments-list">
          <li v-for="att in attachments" :key="att.id">
            <a :href="att.url" target="_blank" rel="noopener" :download="att.name">{{ att.name }}</a>
          </li>
        </ul>
      </div>

      <!-- Conversation button (only for assigned user) -->
      <div v-if="isAssignedToCurrentUser" class="conversation-button-container">
        <ion-button @click="$emit('goToConversation')">
          <ion-icon :icon="icons.chatbubbles || icons.chatbox" slot="start" />
          Ver conversación
        </ion-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject } from 'vue';
import { IonButton, IonBadge, IonSpinner, IonIcon } from '@ionic/vue';

const icons = inject('icons', {});

defineProps({
  selectedMessage: { type: Object, default: null },
  isSupportManager: { type: Boolean, default: false },
  isMobile: { type: Boolean, default: false },
  membersLoading: { type: Boolean, default: false },
  assigning: { type: Boolean, default: false },
  updatingPriority: { type: Boolean, default: false },
  assigneeId: { type: Number, default: null },
  membersError: { type: String, default: '' },
  assignError: { type: String, default: '' },
  assignSuccess: { type: String, default: '' },
  priorityError: { type: String, default: '' },
  prioritySuccess: { type: String, default: '' },
  attachments: { type: Array, default: () => [] },
  attachmentsLoading: { type: Boolean, default: false },
  attachmentsError: { type: String, default: '' },
  isAssignedToCurrentUser: { type: Boolean, default: false },
  formatDate: { type: Function, required: true },
  priorityColor: { type: Function, required: true },
  resolveAssigneeName: { type: Function, required: true }
});

defineEmits(['openAssignPopover', 'openPriorityPopover', 'goToConversation']);
</script>

<style scoped>
.reading-pane {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  max-height: calc(70vh);
}

.no-selection {
  margin: auto;
  text-align: center;
  color: #6b7280;
}

.placeholder-icon {
  font-size: 70px;
  color: #d1d5db;
  margin-bottom: 18px;
}

.reading-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.reading-subject {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  line-height: 1.3;
}

.reading-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.reading-meta {
  margin-top: 8px;
  display: flex;
  gap: 20px;
  font-size: 0.8rem;
  color: #555;
  flex-wrap: wrap;
  align-items: center;
}

.reading-meta .from strong,
.reading-meta .email strong {
  font-weight: 600;
}

.reading-body {
  margin-top: 18px;
  white-space: pre-wrap;
  font-size: 0.82rem;
  line-height: 1.5;
  font-family: var(--ion-font-family, monospace);
  background: #f9fafb;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
}

.reading-meta .from,
.reading-meta .email,
.reading-meta .org,
.reading-meta .prio {
  font-size: 0.95rem;
}

.reading-meta .prio {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  line-height: 1;
}

.reading-meta .prio ion-badge {
  --padding-start: 8px;
  --padding-end: 8px;
  --border-radius: 12px;
  font-size: 0.85rem;
  line-height: 1;
}

.detail-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px 16px;
}

.detail-grid label {
  display: block;
  font-size: 0.7rem;
  color: #6b7280;
}

.detail-grid span {
  font-size: 0.9rem;
  color: #111827;
}

.assign-feedback {
  margin-top: 6px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.success-line {
  color: var(--ion-color-success, #10b981);
  font-size: 0.8rem;
}

.error-line {
  color: var(--ion-color-danger, #ef4444);
  font-size: 0.85rem;
}

.assigned-line {
  margin-top: 6px;
  font-size: 0.85rem;
  color: #374151;
}

.attachments {
  margin-top: 14px;
}

.attachments-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 6px;
}

.attach-icon {
  font-size: 18px;
  color: var(--ion-color-medium, #6b7280);
}

.attachments-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #6b7280;
  font-size: 0.9rem;
}

.attachments-list {
  list-style: none;
  padding: 0;
  margin: 6px 0 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.attachments-list a {
  color: var(--ion-color-primary, #3b82f6);
  text-decoration: none;
}

.attachments-list a:hover {
  text-decoration: underline;
}

.conversation-button-container {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
}

.conversation-button-container ion-button {
  --background: var(--ion-color-primary, #3b82f6);
  --background-hover: #2563eb;
  --color: white;
  font-weight: 600;
  font-size: 0.875rem;
  --padding-start: 12px;
  --padding-end: 16px;
  text-align: center;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: auto;
  min-width: fit-content;
}

.conversation-button-container ion-button ion-icon {
  margin-right: 6px;
}
</style>
