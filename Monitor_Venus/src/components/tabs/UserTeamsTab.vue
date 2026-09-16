<template>
  <div class="content-card">
    <h3 class="content-card-title">
      <ion-icon :icon="icons.people"></ion-icon>
      Equipos y Roles
    </h3>

    <div v-if="teamsLoading" class="teams-state">
      <ion-spinner name="crescent"></ion-spinner>
      <p>Cargando equipos...</p>
    </div>

    <div v-else-if="teamsError" class="teams-state">
      <ion-icon :icon="icons.alertCircle" color="danger" size="large"></ion-icon>
      <p>{{ teamsError }}</p>
      <ion-button @click="fetchTeams" fill="outline" color="primary">Reintentar</ion-button>
    </div>

    <div v-else-if="teams.length" class="teams-grid">
      <div v-for="team in teams" :key="team.role.id || team.role.name" class="team-card"
        :style="{ '--role-color': team.role.color || '#5865F2' }" @click="openTeamModal(team.role)">
        <div class="team-card-header">
          <h4 class="team-role-name">{{ team.role.name }}</h4>
          <div v-if="team.role.color" class="team-color-dot"
            :style="{ backgroundColor: team.role.color }"></div>
        </div>
        <p class="team-role-description">{{ team.role.description || 'Sin descripción' }}</p>
        <div class="team-members">
          <div class="avatar-stack">
            <div v-for="member in team.members.slice(0, 3)" :key="member.id" class="avatar-circle">
              <img v-if="memberAvatarSrc(member.img)" :src="memberAvatarSrc(member.img)"
                :alt="memberFullName(member)" />
              <div v-else class="avatar-initials" :style="{ backgroundColor: memberColor(member) }">
                {{ memberInitials(member) }}
              </div>
            </div>
            <div v-if="team.members.length > 3" class="avatar-circle more-circle">
              +{{ team.members.length - 3 }}
            </div>
          </div>
          <span class="team-member-count">
            <ion-icon :icon="icons.people"></ion-icon>
            {{ team.members.length }}
          </span>
        </div>
      </div>
    </div>

    <div v-else class="teams-state">
      <ion-icon :icon="icons.people" size="large" color="medium"></ion-icon>
      <p>El usuario no tiene roles asignados.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, inject } from 'vue'
import { modalController } from '@ionic/vue'
import API from '@/utils/api/api'
import RoleMembersModal from '@components/forms/roles/RoleMembersModal.vue'

const props = defineProps({
  roles: { type: Array, default: () => [] },
})

const icons = inject('icons', {})

const teams = ref([])
const teamsLoading = ref(false)
const teamsError = ref(null)

const memberAvatarSrc = (img) => {
  if (!img) return null
  if (img.startsWith('http://') || img.startsWith('https://')) return img
  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/'
  const backendUrl = apiBaseUrl.replace(/\/api\/?$/, '')
  const imagePath = img.startsWith('/') ? img : `/${img}`
  return `${backendUrl}${imagePath}`
}

const memberFullName = (member) => {
  const parts = [member.name, member.last_name].filter(Boolean)
  return parts.join(' ') || member.username || member.email || 'Usuario'
}

const memberInitials = (member) => {
  const parts = [member.name, member.last_name].filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  const name = parts[0] || member.username || member.email || 'U'
  return name.substring(0, 2).toUpperCase()
}

const memberColor = (member) => {
  const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#6366f1', '#f97316']
  const name = memberFullName(member)
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

const fetchTeams = async () => {
  const roles = props.roles
  if (!roles.length) {
    teams.value = []
    teamsLoading.value = false
    teamsError.value = null
    return
  }
  teamsLoading.value = true
  teamsError.value = null
  try {
    const results = await Promise.allSettled(
      roles.map(async (role) => {
        const response = await API.get(API.ROLE_MEMBERSHIP(role.id))
        const members = Array.isArray(response) ? response : (response?.data || [])
        return { role, members }
      })
    )
    const loaded = []
    for (const result of results) {
      if (result.status === 'fulfilled') loaded.push(result.value)
    }
    teams.value = loaded
    if (!loaded.length && roles.length) {
      teamsError.value = 'No se pudieron cargar los equipos.'
    }
  } catch (err) {
    teamsError.value = err.message || 'No se pudieron cargar los equipos.'
    teams.value = []
  } finally {
    teamsLoading.value = false
  }
}

watch(() => props.roles, fetchTeams, { immediate: true })

const openTeamModal = async (role) => {
  const modal = await modalController.create({
    component: RoleMembersModal,
    componentProps: { role },
    cssClass: 'full-modal'
  })
  await modal.present()
}
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

.teams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.team-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
  background: var(--ion-card-background, #fff);
  border: 1px solid var(--ion-color-light-shade, #e5e7eb);
  border-top: 3px solid var(--role-color, #5865F2);
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.team-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.team-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.team-role-name {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--ion-text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.team-color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.team-role-description {
  margin: 0;
  font-size: 0.82rem;
  color: var(--ion-color-medium);
  line-height: 1.4;
  min-height: 36px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.team-members {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: auto;
}

.avatar-stack {
  display: flex;
  align-items: center;
}

.avatar-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid var(--ion-card-background, #fff);
  margin-left: -10px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
}

.avatar-circle:first-child {
  margin-left: 0;
}

.avatar-circle img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-initials {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
}

.more-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--ion-color-medium);
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
}

.team-member-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  color: var(--ion-color-medium);
}

.teams-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  text-align: center;
  color: var(--ion-color-medium);
}

.teams-state p {
  margin: 0;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .content-card {
    padding: 16px;
  }
}
</style>
