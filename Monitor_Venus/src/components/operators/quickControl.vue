<template>
  <!--
    Create button (toCreate):
    Opens a modal containing the appropriate create form component.
  -->
  
  <ion-button color="secondary" v-if="toCreate" fill="solid" shape="round" class="mx-2" @click="overlayCreate = !overlayCreate ; selectedAction = 'create'">
    <ion-icon :icon="addOutline" slot="icon-only"></ion-icon>
    
    <ion-modal :is-open="overlayCreate" @did-dismiss="overlayCreate = false">
      <ion-content>
        <div class="d-flex align-center justify-center" style="height: 100vh;">
          <ion-spinner v-if="!componentLoaded" name="circular" color="primary"></ion-spinner>
          <component :is="ComponentToRender.component" v-bind="ComponentToRender.props" @itemCreated="handleItemCreated" @loaded="componentLoaded = true" @closed="overlayCreate = false"/>
        </div>
      </ion-content>
    </ion-modal>
  </ion-button>

  <!--
    Edit button (toEdit):
    Opens a modal containing the appropriate edit form component.
  -->
  <ion-button v-if="toEdit" fill="outline" class="mx-2" @click="overlayEdit = !overlayEdit; selectedAction = 'update';">
    <ion-icon :icon="pencilOutline" slot="start"></ion-icon>
    Editar
    <ion-modal :is-open="overlayEdit" @did-dismiss="overlayEdit = false">
      <ion-content>
        <div class="d-flex align-center justify-center" style="height: 100vh;">
          <ion-spinner v-if="!componentLoaded" name="circular" color="primary"></ion-spinner>
          <component :is="ComponentToRender.component" v-bind="ComponentToRender.props" @itemEdited="handleItemEdited" @loaded="componentLoaded = true"/>
        </div>
      </ion-content>
    </ion-modal>
  </ion-button>

</template>

<script lang="ts">
import { defineComponent, inject } from 'vue';
import { IonButton, IonIcon, IonModal, IonContent, IonSpinner } from '@ionic/vue';
import { addOutline, pencilOutline } from 'ionicons/icons';
import { FormFactory } from '@utils/forms/FormFactory';
import type { ActionType, EntityType } from  '@utils/forms/form-types/formsTypes';

// The 'quickControl' component handles create and edit actions for entities.
export default defineComponent({
  name: 'quickControl',
  components: {
    IonButton,
    IonIcon,
    IonModal,
    IonContent,
    IonSpinner
  },
  emits: ['itemCreated', 'itemEdited'],
  props: {
    /**
     * The type of the item to handle (e.g. 'periodo', 'grupo', 'semillero').
     */
    type: {
      type: String as () => EntityType,
      required: true
    },

    /**
     * The index of the item to handle.
     */
    index: {
      type: Number,
      required: false,
    },

    /**
     * The name of the item to handle.
     */
    name: {
      type: String,
      required: false,
    },

    /**
     * Flag to enable the create action.
     */
    toCreate: {
      type: Boolean,
      required: false,
    },

    /**
     * Flag to enable the edit action.
     */
    toEdit: {
      type: Boolean,
      required: false,
    },

    /**
     * Initial data for the create or edit form (e.g. { name, start_date, ... }).
     */
    initialData: {
      type: Object,
      required: false,
      default: () => ({}),
    }
  },

  setup() {
    return {
      addOutline,
      pencilOutline
    };
  },

  computed: {
    ComponentToRender() {
      const extraProps = {
        index: this.index,
        name: this.name,
        initialData: this.initialData,
      }
      return FormFactory.getComponentConfig(this.selectedAction, this.type, extraProps);
    }
  },

  watch: {
    // Watch for changes in the overlayCreate to load the component
    overlayCreate(newVal) {
      if (newVal) this.componentLoaded = false;
    },
    // Watch for changes in the overlayEdit to load the component
    overlayEdit(newVal) {
      if (newVal) this.componentLoaded = false;
    }
  },

  data() {
    return {
      // Controls the visibility of the create modal
      overlayCreate: false,
      // Controls the visibility of the edit modal
      overlayEdit: false,
      selectedAction: 'create' as ActionType,
      componentLoaded: false,
    };
  },

  methods: {
    /**
     * Handles the 'itemCreated' event from the create form and closes the modal.
     */
    async handleItemCreated() {
      // Close modal first to avoid parent refresh interrupting the modal animation
      this.overlayCreate = false;
      await this.$nextTick();
      this.$emit('itemCreated');
    },

    /**
     * Handles the 'itemEdited' event from the edit form and closes the modal.
     */
    handleItemEdited(index: any, name: any) {
      this.$emit('itemEdited', index, name);
      this.overlayEdit = false;
    },
  }
});
</script>
