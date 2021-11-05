import {iRoute} from "./route";

export interface iMenuItem {
  route: iRoute,
  routeParams?: {[index: string]: string},
  children?: iMenuItem[] | Function,
  label?: string
}
