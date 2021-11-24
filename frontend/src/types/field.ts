import {iAttr} from './attr';
import {iChoice} from './choice';


export interface iField {
  label: string,
  name: string,
  type: 'button' | 'checkbox' | 'color' | 'date' | 'datetime-local' | 'email' | 'file' | 'hidden' | 'image' | 'month' | 'number' | 'password' | 'radio' | 'range' | 'reset' | 'search' | 'submit' | 'tel' | 'text' | 'time' | 'url' | 'week' | 'select' | 'textarea',
  attrs?: iAttr[],
  errors?: string[],
  choices?: iChoice[]
  required?: boolean,
  value?: any
}
