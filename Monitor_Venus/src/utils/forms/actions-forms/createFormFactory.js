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
      /*period: {
        component: CreatePeriod,
        props: {
          type: type,
          label: 'periodo',
          fields: schema.period
        }
      },
      group: {
        component: CreateGroup,
        props: {
          type: type,
          label: "grupo",
          fields: schema.group,
        }
      },
      user_integra: {
        component: CreateUser,
        props: {
          type: type,
          label: "usuario",
          fields: schema.user_integra
        }
      },
      user_external: {
        component: CreateUser,
        props: {
          type: type,
          label: "usuario externo",
          fields: schema.user_external
        }
      },
      role: {
        component: CreateRole,
        props: {
          type: type,
          label: "rol",
          fields: schema.role
        }
      },
      seedbed: {
        component: CreateSeedbed,
        props: {
          type: type,
          label: "semillero",
          fields: schema.seedbed
        }
      },
      functionary_profile: {
        component: CreateInternalProfile,
        props: {
          type: type,
          label: "perfil de funcionario",
          fields: schema.internal_profile
        }
      },
      student_profile: {
        component: CreateInternalProfile,
        props: {
          type: type,
          label: "perfil de estudiante",
          fields: schema.internal_profile
        }
      },
      external_profile: {
        component: CreateExternalProfile,
        props: {
          type: type,
          label: "perfil de aliado externo",
          fields: schema.external_profile
        }
      },
      external_seedbed_profile: {
        component: CreateExternalProfile,
        props: {
          type: type,
          label: "perfil de aliado externo en semillero",
          fields: schema.external_seedbed_profile
        }
      },
      group_profile: {
        component: CreateGroupProfile,
        props: {
          type: type,
          label: "perfil de grupo",
          fields: schema.group_profile
        }
      },
      seedbed_profile: {
        component: CreateSeedbedProfile,
        props: {
          type: type,
          label: "perfil de semillero",
          fields: schema.seedbed_profile
        }
      },
      seedbed_member: {
        component: CreateSeedbedMember,
        props: {
          type: type,
          label: "miembro de semillero",
          fields: schema.seedbed_member
        }
      },*/
    };

    if (!(type in componentMap) || !EntityTypes.includes(type)) {
      console.log(`Componente no encontrado para el tipo: ${type}`);
      return this.getDefaultComponent();
    }

    return componentMap[type];
  }
}
