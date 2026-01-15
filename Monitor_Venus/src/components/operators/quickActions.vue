<template>
  <!--
    View button (toView):
    Displays an icon that redirects to the 'toView' route when clicked.
    If toView is a string, it acts as a router-link. If it's a boolean, it emits a view-clicked event.
  -->
 <ion-buttons>
   <ion-button v-if="toView && typeof toView === 'string'" fill="clear" size="small" :router-link="toView">
    <ion-icon :icon="eyeOutline" slot="icon-only"></ion-icon>
  </ion-button>
  
   <ion-button v-else-if="toView" fill="clear" size="small" @click="handleViewClick">
    <ion-icon :icon="eyeOutline" slot="icon-only"></ion-icon>
  </ion-button>

  <ion-button v-if="toCreate" fill="clear" class="mx-2 rounded-full" @click="overlayCreate = !overlayCreate ; selectedAction = 'create'">
    <ion-icon :icon="addOutline" slot="icon-only"></ion-icon>
    Agregar
    <ion-modal :is-open="overlayCreate" @did-dismiss="overlayCreate = false" class="form-modal">
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
    Opens a modal containing FormUpdateGeneral to update the item.
  -->
  <ion-button v-if="toEdit" fill="clear" size="small" class="action edit" @click="overlayEdit = !overlayEdit; selectedAction = 'update';">
    <ion-icon :icon="createOutline" slot="icon-only"></ion-icon>
    <ion-modal :is-open="overlayEdit" @did-dismiss="overlayEdit = false" class="form-modal">
      <ion-content>
        <div class="d-flex align-center justify-center" style="height: 100vh;">
          <ion-spinner v-if="!componentLoaded" name="circular" color="primary"></ion-spinner>
          <component :is="ComponentToRender.component" v-bind="ComponentToRender.props" @itemEdited="handleItemEdited" @loaded="componentLoaded = true" @closed="overlayEdit = false"/>
        </div>
      </ion-content>
    </ion-modal>
    <!--<ion-tooltip>
      Editar
    </ion-tooltip>-->
  </ion-button>

  <!--
    Delete button (toDelete):
    Opens a modal with FormDeleteGeneral to perform a delete action.
  -->
  <ion-button v-if="toDelete" fill="clear" size="small" class="action delete" @click="overlayDelete = !overlayDelete ; selectedAction = 'delete'">
    <ion-icon :icon="trashOutline" slot="icon-only"></ion-icon>
    <ion-modal :is-open="overlayDelete" @did-dismiss="overlayDelete = false" class="form-modal">
      <ion-content>
        <div class="d-flex align-center justify-center" style="height: 100vh;">
          <ion-spinner v-if="!componentLoaded" name="circular" color="primary"></ion-spinner>
          <component :is="ComponentToRender.component" v-bind="ComponentToRender.props" @itemDeleted="handleItemDeleted" @loaded="componentLoaded = true" @closed="overlayDelete = false"/>
        </div>
      </ion-content>
    </ion-modal>
    <!--<ion-tooltip>
      Eliminar
    </ion-tooltip>-->
  </ion-button>
  </ion-buttons>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { IonButton, IonIcon, IonModal, IonContent, IonSpinner, IonButtons } from '@ionic/vue';
import { eyeOutline, addOutline, createOutline, trashOutline } from 'ionicons/icons';
import { FormFactory } from '@utils/forms/FormFactory';
import type { ActionType, EntityType } from '@utils/forms/form-types/formsTypes';


// The 'quickActions' component centralizes quick actions (view, edit, delete).
export default defineComponent({
  name: 'quickActions',
  components: {
    IonButton,
    IonIcon,
    IonModal,
    IonContent,
    IonSpinner,
    //IonTooltip,
    IonButtons
  },
  emits: ['itemCreated', 'itemDeleted', 'itemEdited', 'view-clicked'],
  props: {
    /**
     * The type of the item to handle (e.g. 'periodo', 'grupo', 'semillero').
     */
    type:
    { type: String as () => EntityType,
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
     * Here are the props received by the component, organized by prefixes:
     * to: index of the item to handle
     * type: type of the item to handle
     * item: name of the item to handle
     */
    // ---[View]---
    toView: {
      type: [String, Boolean],
      required: false,
    },
    //--[Create]---
    toCreate: {
      type: Boolean,
      required: false,
    },
    toEdit: {
      type: Boolean,
      required: false,
    },
    // ---[Delete]---
    toDelete: {
      type: Boolean,
      required: false,
    },
    /**
     * Initial data for the edit form (e.g. { name, start_date, ... }).
     */
    initialData: {
      type: Object,
      required: false,
      default: () => ({}),
    }
  },
  setup() {
    return {
      eyeOutline,
      addOutline,
      createOutline,
      trashOutline
    };
  },
  computed: {
    ComponentToRender(){
      const extraProps = {
        index: this.index,
        name: this.name,
        initialData: this.initialData,
      }
      return FormFactory.getComponentConfig(this.selectedAction, this.type, extraProps);
    }
  },
  watch : {
    // Watch for changes in the selectedAction to load the component
    overlayCreate(newVal) {
      if (newVal) this.componentLoaded = false;
    },
    overlayEdit(newVal) {
      if (newVal) this.componentLoaded = false;
    },
    overlayDelete(newVal) {
      if (newVal) this.componentLoaded = false;
    }
  },
  data() {
    return {
      // ---[Modals]---
      // Controls the visibility of the create modal
      overlayCreate: false,
      // Controls the visibility of the edit modal
      overlayEdit: false,
      // Controls the visibility of the delete modal
      overlayDelete: false,
      //----
      selectedAction: '' as ActionType,

      componentLoaded: false,

    };
  },

  methods: {
    handleViewClick() {
      this.$emit('view-clicked');
    },
    runfetch() {
      // 1) Select the update action
      // 3) Once modal is set to true, call the child's runFetchMapData
      this.$nextTick(() => {
        const child = this.$refs.updateGlobalGroupRef as any
        if (child && typeof child.runFetchMapData === 'function') {
          child.runFetchMapData()
        }
      })
    },
    /**
     * Handles the 'itemCreated' event from FormUpdateGeneral and closes the modal.
     */
    handleItemCreated() {
      this.$emit('itemCreated');
      this.overlayCreate = false;
    },
    /**
     * Handles the 'itemDeleted' event from FormDeleteGeneral and closes the modal.
     */
    handleItemDeleted(index: any) {
      this.$emit('itemDeleted', index);
      this.overlayDelete = false;
    },

    /**
     * Handles when an item is edited in FormUpdateGeneral and closes the modal.
     */
    handleItemEdited(index: any, name: any) {
      this.$emit('itemEdited', index, name);
      this.overlayEdit = false;
    },

  }
});
</script>
