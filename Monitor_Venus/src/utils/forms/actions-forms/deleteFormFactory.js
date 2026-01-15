// src/factories/DeleteComponentFactory.js
import { AbstractFormFactory } from "../abstractFormsFactory.js";
import { defineAsyncComponent } from "vue";
import { EntityTypes } from '../form-types/formsTypes.js';

const DeleteComponent = defineAsyncComponent(() => import("@/components/forms/delete/formDelete.vue"));

export class DeleteFormFactory extends AbstractFormFactory {
  getComponentConfig(type, extraProps = {}) {
    const componentMap = {
      tenant: {
        component: DeleteComponent,
        props: {
          name: extraProps?.name,
          type: type,
          label: "tenant",
          index: extraProps?.index,
        }
      },
      workspace: {
        component: DeleteComponent,
        props: {
          name: extraProps?.name,
          type: type,
          label: "workspace",
          index: extraProps?.index,
        }
      },
      location: {
        component: DeleteComponent,
        props: {
          name: extraProps?.name,
          type: type,
          label: "location",
          index: extraProps?.index,
        }
      },
      gateway: {
        component: DeleteComponent,
        props: {
          name: extraProps?.name,
          type: type,
          label: "gateway",
          index: extraProps?.index,
        }
      },
      device_profile: {
        component: DeleteComponent,
        props: {
          name: extraProps?.name,
          type: type,
          label: "device profile",
          index: extraProps?.index,
        }
      },
      application: {
        component: DeleteComponent,
        props: {
          name: extraProps?.name,
          type: type,
          label: "application",
          index: extraProps?.index,
        }
      },
      device: {
        component: DeleteComponent,
        props: {
          name: extraProps?.name,
          type: type,
          label: "device",
          index: extraProps?.index,
        }
      },
      machine: {
        component: DeleteComponent,
        props: {
          name: extraProps?.name,
          type: type,
          label: "machine",
          index: extraProps?.index,
        }
      },
      role: {
        component: DeleteComponent,
        props: {
          name: extraProps?.name,
          type: type,
          label: "role",
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


