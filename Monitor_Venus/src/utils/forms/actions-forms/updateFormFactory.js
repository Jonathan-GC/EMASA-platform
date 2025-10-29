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
export class UpdateFormFactory extends AbstractFormFactory {
  getComponentConfig(type, extraProps = {}) {
    const componentMap = {
      tenant: {
        component: defineAsyncComponent(() => import("@components/forms/update/tenants/formUpdateTenants.vue")),
        props: {
          type: type,
          index: extraProps?.index,
          label: 'tenant',
          fields: schema.tenant,
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
