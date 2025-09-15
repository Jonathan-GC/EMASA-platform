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
export class UpdateFormFactory extends AbstractFormFactory {
  getComponentConfig(type, extraProps = {}) {
    const componentMap = {
        period: {
          component: UpdatePeriod,
          props: {
            type: type,
            label: "periodo",
            fields: schema.period,
            index: extraProps.index,
            initialData: extraProps.initialData,
          }
        },
        group: {
          component: UpdateGroup,
          props: {
            type: type,
            label: "grupo",
            fields: schema.group,
            index: extraProps.index,
            initialData: extraProps.initialData,
          }
        },
        seedbed: {
          component: UpdateSeedbed,
          props: {
            type: type,
            label: "semillero",
            fields: schema.seedbed,
            index: extraProps.index,
            initialData: extraProps.initialData,
          }
        },
        group_profile: {
          component: UpdateGroupProfile,
          props: {
            type: type,
            label: "perfil de grupo",
            fields: schema.group_profile,
            index: extraProps.index,
            initialData: extraProps.initialData,
          }
        },
        seedbed_profile: {
          component: UpdateSeedbedProfile,
          props: {
            type: type,
            label: "perfil de semillero",
            fields: schema.seedbed_profile,
            index: extraProps.index,
            initialData: extraProps.initialData,
          }
        },
        seedbed_coordinator: {
          component: UpdateSeedbedProfile,
          props: {
            type: type,
            label: "coordinador de semillero",
            fields: schema.seedbed_coordinator,
            index: extraProps.index,
            initialData: extraProps.initialData,
          }
        },
        seedbed_tutor: {
          component: UpdateSeedbedProfile,
          props: {
            type: type,
            label: "Tutor de semillero",
            fields: schema.seedbed_tutor,
            index: extraProps.index,
            initialData: extraProps.initialData,
          }
        }
    };

    if (!(type in componentMap) || !EntityTypes.includes(type)) {
      console.log(`Componente no encontrado para el tipo: ${type}`);
      return this.getDefaultComponent();
    }

    return componentMap[type];
  }
}
