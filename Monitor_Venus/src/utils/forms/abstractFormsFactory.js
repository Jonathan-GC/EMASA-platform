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
          return h('div', {
            style: {
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              width: '100%',
              height: '200px',
              textAlign: 'center',
              color: 'var(--ion-color-medium, #666)'
            }
          }, 'Formulario no encontrado');
        }
        
      }),
      props: {}
    };
  }
}
