import {iAttr} from './attr';
import {iChoice} from './choice';


export interface iField {
  id?: string,
  label: string,
  name: string,
  type: 'button' | 'checkbox' | 'color' | 'date' | 'datetime-local' | 'email' | 'file' | 'hidden' | 'image' | 'month' | 'number' | 'password' | 'radio' | 'range' | 'reset' | 'search' | 'submit' | 'tel' | 'text' | 'time' | 'url' | 'week' | 'select' | 'textarea',
  attrs?: iAttr[],
  errors?: string[],
  choices?: iChoice[]
  required?: boolean,
  value?: any,
  defaultValue?: any,
  selected?: boolean,
  defaultSelected?: boolean,
  onChange: Function,
}
