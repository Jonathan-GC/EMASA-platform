// src/factories/DeleteComponentFactory.js
import { AbstractFormFactory } from "../abstractFormsFactory.js";
import { defineAsyncComponent } from "vue";
import { EntityTypes } from '../form-types/formsTypes.js';

const ToggleComponent = defineAsyncComponent(() => import("@/components/forms/toggle/formToggle.vue"));

export class ToggleFormFactory extends AbstractFormFactory {
  getComponentConfig(type, extraProps = {}) {
    const componentMap = {
      user: {
        component: ToggleComponent,
        props: {
          name: extraProps?.name,
          type: type,
          label: "usuario",
          status: extraProps?.status,
          index: extraProps?.index,
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


