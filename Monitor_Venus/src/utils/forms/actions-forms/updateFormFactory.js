// src/factories/UpdateComponentFactory.js

import { defineAsyncComponent } from "vue";
import { AbstractFormFactory } from "../abstractFormsFactory.js";
import { EntityTypes } from '../form-types/formsTypes.js';
import schema from '@/schemas/formUpdateSchemas.json';

/*mconst UpdatePeriod = defineAsyncComponent(() => import("@/components/forms/update/formUpdateGeneral.vue"));
const UpdateGroup = defineAsyncComponent(() => import("@/components/forms/update/groups/formUpdateGroups.vue"));
const UpdateSeedbed = defineAsyncComponent(() => import("@/components/forms/update/seedbeds/formUpdateSeedbeds.vue"));
const UpdateGroupProfile = defineAsyncComponent(() => import("@/components/forms/update/groups/formUpdateGroupProfile.vue"));
const UpdateSeedbedProfile = defineAsyncComponent(() => import("@/components/forms/update/seedbeds/formUpdateSeedbedProfile.vue"));
*/
const UpdateTenants = defineAsyncComponent(() => import("@components/forms/update/tenants/formUpdateTenants.vue"));
const UpdateWorkspaces = defineAsyncComponent(() => import("@components/forms/update/workspaces/formUpdateWorkspaces.vue"));
const UpdateLocations = defineAsyncComponent(() => import("@components/forms/update/locations/formUpdateLocations.vue"));
const UpdateGateways = defineAsyncComponent(() => import("@components/forms/update/gateways/formUpdateGateways.vue"));
const UpdateApplications = defineAsyncComponent(() => import("@components/forms/update/application/formUpdateApplication.vue"));
const UpdateDevices = defineAsyncComponent(() => import("@components/forms/update/device/formUpdateDevices.vue"));
const UpdateMachines = defineAsyncComponent(() => import("@components/forms/update/machines/formUpdateMachines.vue"));
const UpdateMeasurements = defineAsyncComponent(() => import("@components/forms/update/measurements/formUpdateMeasurements.vue"));
const UpdateRoles = defineAsyncComponent(() => import("@components/forms/update/roles/formUpdateRoles.vue"));
const UpdateDeviceTypes = defineAsyncComponent(() => import("@components/forms/update/device_types/formUpdateDeviceType.vue"));
const UpdateUsers = defineAsyncComponent(() => import("@components/forms/update/users/formUpdateUsers.vue"));

export class UpdateFormFactory extends AbstractFormFactory {
  getComponentConfig(type, extraProps = {}) {
    const componentMap = {
      tenant: {
        component: UpdateTenants,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'cliente',
          fields: schema.tenant,
          initialData: extraProps?.initialData || {},
        }
      },
      workspace: {
        component: UpdateWorkspaces,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'workspace',
          fields: schema.workspace,
          initialData: extraProps?.initialData || {},
        }
      },
      location: {
        component: UpdateLocations,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'ubicación',
          fields: schema.location,
          initialData: extraProps?.initialData || {},
        }
      },
      gateway: {
        component: UpdateGateways,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'gateway',
          fields: schema.gateway,
          initialData: extraProps?.initialData || {},
        }
      },
      device_profile: {
        component: UpdateGateways,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'perfil de dispositivo',
          fields: schema.device_profile,
          initialData: extraProps?.initialData || {},
        }
      },
      application: {
        component: UpdateApplications,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'servicio',
          fields: schema.application,
          initialData: extraProps?.initialData || {},
        }
      },
      device: {
        component: UpdateDevices,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'dispositivo',
          fields: schema.device,
          initialData: extraProps?.initialData || {},
        }
      },
      device_type: {
        component: UpdateDeviceTypes,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'tipo de dispositivo',
          fields: schema.device_type,
          initialData: extraProps?.initialData || {},
        }
      },
      measurement: {
        component: UpdateMeasurements,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'variable',
          fields: schema.measurement,
          initialData: extraProps?.initialData || {},
        }
      },
      machine: {
        component: UpdateMachines,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'máquina',
          fields: schema.machine,
          initialData: extraProps?.initialData || {},
        }
      },
      role: {
        component: UpdateRoles,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'rol',
          fields: schema.role,
          initialData: extraProps?.initialData || {},
        }
      },
      user: {
        component: UpdateUsers,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'usuario',
          fields: schema.user,
          initialData: extraProps?.initialData || {},
        }
      },
    }
    if (!(type in componentMap) || !EntityTypes.includes(type)) {
      console.log(`Componente no encontrado para el tipo: ${type}`);
      return this.getDefaultComponent();
    }

    return componentMap[type];
  }
}
