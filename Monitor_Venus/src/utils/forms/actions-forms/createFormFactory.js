// src/factories/CreateComponentFactory.js
import { AbstractFormFactory } from "../abstractFormsFactory.js";
import { defineAsyncComponent } from "vue";
import { EntityTypes } from '../form-types/formsTypes.js';
import schema from '@/schemas/formCreateSchemas.json';

//const CreatePeriodo = defineAsyncComponent(() => import("@/components/forms/create/formCreateGeneral.vue"));
/*const CreatePeriod = defineAsyncComponent(() => import("@/components/forms/create/Periods/formCreatePeriods.vue"));
const CreateGroup = defineAsyncComponent(() => import("@/components/forms/create/Groups/formCreateGroups.vue"));
const CreateSeedbed = defineAsyncComponent(() => import("@/components/forms/create/seedbeds/formCreateSeedbed.vue"));
const CreateUser = defineAsyncComponent(() => import("@/components/forms/create/Users/formCreateUsers.vue"));
const CreateRole = defineAsyncComponent(() => import("@/components/forms/create/Roles/formCreateRoles.vue"));
const CreateInternalProfile = defineAsyncComponent(() => import("@/components/forms/create/Users/formCreateInternalProfile.vue"));
const CreateExternalProfile = defineAsyncComponent(() => import("@/components/forms/create/Users/formCreateExternalProfile.vue"));
const CreateGroupProfile = defineAsyncComponent(() => import("@/components/forms/create/Groups/formCreateGroupProfile.vue"));
const CreateSeedbedProfile = defineAsyncComponent(() => import("@/components/forms/create/seedbeds/formCreateSeedbedProfile.vue"));
const CreateSeedbedMember = defineAsyncComponent(() => import("@/components/forms/create/seedbeds/formCreateSeedbedMember.vue"));
*/

const CreateTenants = defineAsyncComponent(() => import("@components/forms/create/tenants/formCreateTenants.vue"));
const CreateGateways = defineAsyncComponent(() => import("@components/forms/create/gateways/formCreateGateways.vue"));
const CreateLocations = defineAsyncComponent(() => import("@components/forms/create/locations/formCreateLocations.vue"));
const CreateDeviceProfiles = defineAsyncComponent(() => import("@components/forms/create/device_profiles/formCreateDeviceProfiles.vue"));



export class CreateFormFactory extends AbstractFormFactory {
    getComponentConfig(type) {
        const componentMap = {
            tenant: {
                component: CreateTenants,
                props: {
                    type: type,
                    label: 'tenant',
                    fields: schema.tenant,
                }
            },
            gateway: {
                component: CreateGateways,
                props: {
                    type: type,
                    label: 'gateway',
                    fields: schema.gateway,
                }
            },
            location: {
                component: CreateLocations,
                props: {
                    type: type,
                    label: 'location',
                    fields: schema.location,
                }
            },
            device_profile: {
                component: CreateDeviceProfiles,
                props: {
                    type: type,
                    label: 'device profile',
                    fields: schema.device_profile,
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
