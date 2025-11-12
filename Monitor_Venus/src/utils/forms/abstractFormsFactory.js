// src/factories/AbstractComponentFactory.js
import { defineComponent, h } from "vue";

export class AbstractFormFactory {
  getComponentConfig(type, extraProps = {}) {
    throw new Error("getComponentConfig method must be implemented by subclass");
  }

  getDefaultComponent() {
    return {
      component: defineComponent({
        render() {
          this.$emit('loaded');
          return h('div', 'Formulario no encontrado');
        }
        
      }),
      props: {}
    };
  }
}
