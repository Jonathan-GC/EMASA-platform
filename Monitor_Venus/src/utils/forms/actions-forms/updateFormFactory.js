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
export class UpdateFormFactory extends AbstractFormFactory {
  getComponentConfig(type, extraProps = {}) {
    const componentMap = {
      tenant: {
        component: UpdateTenants,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'tenant',
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
          label: 'location',
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
          label: 'device_profile',
          fields: schema.device_profile,
          initialData: extraProps?.initialData || {},
        }
      },
      application: {
        component: UpdateGateways,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'application',
          fields: schema.application,
          initialData: extraProps?.initialData || {},
        }
      },
      device: {
        component: UpdateGateways,
        props: {
          type: type,
          index: extraProps?.index,
          label: 'device',
          fields: schema.device,
          initialData: extraProps?.initialData || {},
        }
      }
    }
    if (!(type in componentMap) || !EntityTypes.includes(type)) {
      console.log(`Componente no encontrado para el tipo: ${type}`);
      return this.getDefaultComponent();
    }

    return componentMap[type];
  }
}
