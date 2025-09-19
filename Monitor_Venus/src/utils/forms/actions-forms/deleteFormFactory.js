// src/factories/DeleteComponentFactory.js
import { AbstractFormFactory } from "../abstractFormsFactory.js";
import { defineAsyncComponent } from "vue";
import { EntityTypes } from '../form-types/formsTypes.js';

/*const DeleteComponent = defineAsyncComponent(() => import("@/components/forms/delete/formDeleteGeneral.vue"));
*/
export class DeleteFormFactory extends AbstractFormFactory {
  getComponentConfig(type, extraProps = {}) {
    const componentMap = {
      period: {
        component: DeleteComponent,
        props: {
          name: extraProps.name,
          type: type,
          label: "periodo",
          index: extraProps.index,
        }
      },
      group: {
        component: DeleteComponent,
        props: {
          name: extraProps.name,
          type: type,
          label: "grupo",
          index: extraProps.index,
        }
      },
      seedbed: {
        component: DeleteComponent,
        props: {
          name: extraProps.name,
          type: type,
          label: "semillero",
          index: extraProps.index,
        }
      },
      group_profile: {
        component: DeleteComponent,
        props: {
          name: extraProps.name,
          type: type,
          label: "perfil de grupo",
          index: extraProps.index,
        }
      },
      seedbed_profile: {
        component: DeleteComponent,
        props: {
          name: extraProps.name,
          type: type,
          label: "perfil de semillero",
          index: extraProps.index,
        }
      },
    };

    if (!(type in componentMap) || !EntityTypes.includes(type)) {
      console.log(`Componente no encontrado para el tipo: ${type}`);
      return this.getDefaultComponent();
    }

    return componentMap[type];
  }
}


