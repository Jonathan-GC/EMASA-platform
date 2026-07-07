<template>
    <div class="message-list-container">
        <!-- Action buttons -->
        <div class="list-actions">
            <!-- Refresh button on the left -->
            <ion-button fill="clear" class="mail-buttons" shape="round" @click="$emit('refresh')"
                title="Refrescar" size="small">
                <ion-icon :icon="icons.refresh" slot="icon-only" />
            </ion-button>

            <!-- Spacer to push controls to the right -->
            <div class="actions-spacer"></div>

            <!-- Filter and sort controls on the right -->
            <div class="actions-right">
                <ion-button fill="clear" shape="round" @click="$emit('toggle-unread')"
                    :color="showUnreadOnly ? 'primary' : 'medium'" size="small"
                    :title="showUnreadOnly ? 'Mostrar todos' : 'Mostrar no leídos'">
                    <ion-icon :icon="showUnreadOnly ? icons.eye : icons.eyeOff" slot="icon-only" />
                </ion-button>
                <ion-button fill="clear" class="mail-buttons" shape="round" @click="$emit('clear-search')"
                    :disabled="!hasSearch" title="Limpiar búsqueda" size="small">
                    <ion-icon :icon="icons.sync" slot="icon-only" />
                </ion-button>

                <!-- Sort by button -->
                <ion-button id="sort-trigger" class="mail-buttons" fill="clear" shape="round"
                    @click="openSortPopover($event)" title="Ordenar por" size="small">
                    <ion-icon :icon="icons.funnel || icons.filter" slot="icon-only" />
                </ion-button>

                <!-- Sort direction button -->
                <ion-button fill="clear" class="mail-buttons" shape="round" @click="$emit('toggle-sort-direction')"
                    :title="sortAscending ? 'Orden descendente' : 'Orden ascendente'" size="small">
                    <ion-icon :icon="sortAscending ? icons.upload : icons.down" slot="icon-only" />
                </ion-button>
            </div>
        </div>

        <!-- Sort popover -->
        <ion-popover :is-open="sortPopoverOpen" :event="sortPopoverEvent" @didDismiss="sortPopoverOpen = false">
            <ion-content>
                <ion-list>
                    <ion-list-header>
                        <ion-label>Ordenar por</ion-label>
                    </ion-list-header>
                    <ion-item button @click="handleSortSelection('date')">
                        <ion-icon :icon="icons.calendar || icons.time" slot="start" />
                        <ion-label>Fecha</ion-label>
                        <ion-icon v-if="currentSortField === 'date'" :icon="icons.checkmark" slot="end"
                            color="primary" />
                    </ion-item>
                    <ion-item button @click="handleSortSelection('from')">
                        <ion-icon :icon="icons.person" slot="start" />
                        <ion-label>Usuario</ion-label>
                        <ion-icon v-if="currentSortField === 'from'" :icon="icons.checkmark" slot="end"
                            color="primary" />
                    </ion-item>
                    <ion-item button @click="handleSortSelection('organization')">
                        <ion-icon :icon="icons.business || icons.briefcase" slot="start" />
                        <ion-label>Organización</ion-label>
                        <ion-icon v-if="currentSortField === 'organization'" :icon="icons.checkmark" slot="end"
                            color="primary" />
                    </ion-item>
                    <ion-item button @click="handleSortSelection('priority')">
                        <ion-icon :icon="icons.flag || icons.alert" slot="start" />
                        <ion-label>Prioridad</ion-label>
                        <ion-icon v-if="currentSortField === 'priority'" :icon="icons.checkmark" slot="end"
                            color="primary" />
                    </ion-item>
                    <ion-item button @click="handleSortSelection('subject')">
                        <ion-icon :icon="icons.document || icons.documentText" slot="start" />
                        <ion-label>Asunto</ion-label>
                        <ion-icon v-if="currentSortField === 'subject'" :icon="icons.checkmark" slot="end"
                            color="primary" />
                    </ion-item>
                    <ion-item button @click="handleSortSelection('status')">
                        <ion-icon :icon="icons.checkmarkCircle || icons.checkbox" slot="start" />
                        <ion-label>Estado</ion-label>
                        <ion-icon v-if="currentSortField === 'status'" :icon="icons.checkmark" slot="end"
                            color="primary" />
                    </ion-item>
                </ion-list>
            </ion-content>
        </ion-popover>

        <div class="message-list" :class="{ 'empty': filteredMessages.length === 0 }">
            <template v-if="filteredMessages.length">
                <div v-for="msg in filteredMessages" :key="msg.id"
                    :class="['message-item', { selected: msg.id === selectedId, unread: msg.unread }]"
                    @click="$emit('select', msg.id)">
                    <div class="message-main">
                        <div class="from-subject">
                            <span class="from">{{ msg.from }}</span>
                            <div class="subject">
                                <span>{{ msg.subject }}</span>
                                <ion-badge class="prio" :color="priorityColor(msg.priority)">{{ msg.priority
                                    }}</ion-badge>
                            </div>
                        </div>
                        <div class="meta-row">
                            <span class="date">{{ formatDate(msg.date) }}</span>
                            <span v-if="msg.unread" class="dot" title="Unread"></span>
                        </div>
                    </div>
                    <div class="snippet">{{ msg.organization || msg.snippet }}</div>
                </div>
            </template>
            <div v-else class="empty-state">
                <ion-icon :icon="icons.inbox" class="empty-icon" />
                <p>Ningún mensaje coincide con tu búsqueda.</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, inject } from 'vue';
import { IonBadge, IonIcon, IonButton, IonPopover, IonContent, IonList, IonListHeader, IonItem, IonLabel } from '@ionic/vue';

const icons = inject('icons', {});

// Popover state
const sortPopoverOpen = ref(false);
const sortPopoverEvent = ref(null);

const props = defineProps({
    filteredMessages: { type: Array, required: true },
    selectedId: { type: Number, default: null },
    formatDate: { type: Function, required: true },
    priorityColor: { type: Function, required: true },
    hasSearch: { type: Boolean, default: false },
    showUnreadOnly: { type: Boolean, default: false },
    currentSortField: { type: String, default: 'date' },
    sortAscending: { type: Boolean, default: false }
});

const emit = defineEmits(['select', 'clear-search', 'toggle-unread', 'refresh', 'sort-by', 'toggle-sort-direction']);

function openSortPopover(event) {
    sortPopoverEvent.value = event;
    sortPopoverOpen.value = true;
}

function handleSortSelection(field) {
    emit('sort-by', field);
    sortPopoverOpen.value = false;
}
</script>

<style scoped>
.message-list-container {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.list-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 12px;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-bottom: none;
    border-radius: 14px 14px 0 0;
}

.actions-spacer {
    flex: 1;
}

.actions-right {
    display: flex;
    align-items: center;
    gap: 4px;
}

.list-actions ion-button {
    --padding-start: 8px;
    --padding-end: 8px;
}

.message-list {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 0 0 14px 14px;
    padding: 8px 0;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    max-height: calc(70vh);
    text-align: left;
}

ion-button.mail-buttons {
    --color: black !important;
    --ripple-color: orange !important;
}

.message-item {
    padding: 10px 14px 8px;
    cursor: pointer;
    border-bottom: 1px solid #f1f5f9;
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 4px;
    text-align: left;
    align-items: flex-start;
}

.message-item:last-child {
    border-bottom: none;
}

.message-item:hover {
    background: #f8fafc;
}

.message-item.selected {
    background: #eef6ff;
}

.message-item.unread .subject {
    font-weight: 600;
}

.message-main {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    width: 100%;
}

.from-subject {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
    width: 100%;
    max-width: 100%;
}

.from {
    font-size: 0.75rem;
    color: #555;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
}

.subject {
    font-size: 0.95rem;
    color: #111;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: flex;
    align-items: center;
    gap: 8px;
    max-width: 100%;
}

.subject>span:first-child {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0;
}

.meta-row {
    display: flex;
    align-items: center;
    gap: 6px;
}

.date {
    font-size: 0.7rem;
    color: #888;
}

.dot {
    width: 8px;
    height: 8px;
    background: var(--ion-color-primary);
    border-radius: 50%;
}

.snippet {
    font-size: 0.85rem;
    color: #555;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.message-item .subject .prio {
    margin-left: 8px;
    text-transform: capitalize;
    font-size: 0.9rem;
}

ion-badge.prio {
    --padding-start: 6px;
    --padding-end: 6px;
    --border-radius: 12px;
    font-size: 0.78rem;
    line-height: 1;
    display: inline-flex;
    align-items: center;
}

.from {
    font-size: 0.9rem;
    font-weight: 500;
}

.message-list.empty {
    align-items: center;
    justify-content: center;
}

.empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #6b7280;
}

.empty-icon {
    font-size: 64px;
    color: #d1d5db;
    margin-bottom: 10px;
}

@media (max-width: 768px) {
    .message-item .item-actions {
        display: none;
    }
}
</style>
