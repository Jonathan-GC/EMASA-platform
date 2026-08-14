/**
 * Activity Mappings
 * Friendly Spanish labels for audit log values, so the user activity
 * timeline reads naturally for non-technical users.
 */

export const OBJECT_TYPE_LABELS = {
  device: { label: 'dispositivo', article: 'el' },
  gateway: { label: 'pasarela', article: 'la' },
  machine: { label: 'máquina', article: 'la' },
  application: { label: 'aplicación', article: 'la' },
  location: { label: 'ubicación', article: 'la' },
  user: { label: 'usuario', article: 'el' },
  tenant: { label: 'organización', article: 'la' },
  workspace: { label: 'espacio de trabajo', article: 'el' },
  role: { label: 'rol', article: 'el' },
  type: { label: 'tipo de dispositivo', article: 'el' },
  devicetype: { label: 'tipo de dispositivo', article: 'el' },
  deviceprofile: { label: 'perfil de dispositivo', article: 'el' },
  ticket: { label: 'ticket', article: 'el' },
  comment: { label: 'comentario', article: 'el' },
  subscription: { label: 'suscripción', article: 'la' },
  permission: { label: 'permiso', article: 'el' },
  notification: { label: 'notificación', article: 'la' }
};

export const MODULE_LABELS = {
  infrastructure: 'Infraestructura',
  users: 'Usuarios',
  roles: 'Roles',
  organizations: 'Organizaciones',
  support: 'Soporte',
  notifications: 'Notificaciones',
  auth: 'Autenticación'
};

const normalize = (value) => String(value || '').toLowerCase().replace(/[^a-z]/g, '');

export const getObjectType = (model) => {
  if (!model) return null;
  return OBJECT_TYPE_LABELS[normalize(model)] || null;
};

export const getModuleLabel = (app) => {
  if (!app) return 'Sistema';
  const key = normalize(app);
  return MODULE_LABELS[key] || (app.charAt(0).toUpperCase() + app.slice(1));
};

export default {
  OBJECT_TYPE_LABELS,
  MODULE_LABELS,
  getObjectType,
  getModuleLabel
};
