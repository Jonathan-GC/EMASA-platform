// src/factories/ComponentFactory.js
import { AbstractFormFactory } from "./abstractFormsFactory.js";
import { CreateFormFactory } from "./actions-forms/createFormFactory.js";
import { UpdateFormFactory } from "./actions-forms/updateFormFactory.js";
import { DeleteFormFactory } from "./actions-forms/deleteFormFactory.js";

export class FormFactory {
  static getFactory(action) {
    const factoryMap = {
      create: new CreateFormFactory(),
      update: new UpdateFormFactory(),
      view: new CreateFormFactory(), // Using create as fallback for view
      delete: new DeleteFormFactory()
    };

    return factoryMap[action] || new CreateFormFactory(); // Fallback to "create"
  }

  static getComponentConfig(action, type, extraProps = {}) {
    return this.getFactory(action).getComponentConfig(type, extraProps);
  }
}
