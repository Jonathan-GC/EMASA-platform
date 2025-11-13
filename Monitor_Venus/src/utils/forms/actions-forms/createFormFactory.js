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
const CreateDevices = defineAsyncComponent(() => import("@components/forms/create/device/formCreateDevices.vue"));
const CreateDeviceActivation = defineAsyncComponent(() => import("@components/forms/create/device/formActivationDevice.vue"));
const CreateMachines = defineAsyncComponent(() => import("@components/forms/create/machines/formCreateMachines.vue"));
const CreateApplications = defineAsyncComponent(() => import("@components/forms/create/applications/formCreateApplications.vue"));
const CreateWorkspaces = defineAsyncComponent(() => import("@components/forms/create/workspaces/formCreateWorkspaces.vue"));
const CreateManagers = defineAsyncComponent(() => import("@components/forms/create/managers/formCreateManagers.vue"));
const CreateUsers = defineAsyncComponent(() => import("@components/forms/create/users/formCreateUsers.vue"));
const CreateMeasurements = defineAsyncComponent(() => import("@components/forms/create/measurements/formCreateMeasurements.vue"));


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
            },
            device: {
                component: CreateDevices,
                props: {
                    type: type,
                    label: 'device',
                    fields: schema.device,
                }
            },
            device_activation: {
                component: CreateDeviceActivation,
                props: {
                    type: type,
                    label: 'device activation',
                    fields: schema.device_activation,
                }
            },
            machine: {
                component: CreateMachines,
                props: {
                    type: type,
                    label: 'machine',
                    fields: schema.machine,
                }
            },
            application: {
                component: CreateApplications,
                props: {
                    type: type,
                    label: 'application',
                    fields: schema.application,
                }
            },
            workspace: {
                component: CreateWorkspaces,
                props: {
                    type: type,
                    label: 'workspace',
                    fields: schema.workspace,
                }
            },
            manager: {
                component: CreateManagers,
                props: {
                    type: type,
                    label: 'manager',
                    fields: schema.manager,
                }
            },
            user: {
                component: CreateUsers,
                props: {
                    type: type,
                    label: 'usuario',
                    fields: schema.user,
                }
            },
            measurement: {
                component: CreateMeasurements,
                props: {
                    type: type,
                    label: 'measurement',
                    fields: schema.measurement,
                }
            },   
        }

        if (!(type in componentMap) || !EntityTypes.includes(type)) {
            console.log(`Componente no encontrado para el tipo: ${type}`);
            return this.getDefaultComponent();
        }
        return componentMap[type];
    }
}
