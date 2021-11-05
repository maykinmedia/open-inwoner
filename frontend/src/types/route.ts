import {ComponentType} from "react";

export interface iRoute {
  component: ComponentType
  label: string|Function,
  path: string,
  exact?: boolean,
  icon?: ComponentType,
  loginRequired?: boolean
  meta?: Object,
}
