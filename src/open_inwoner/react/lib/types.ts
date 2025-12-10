// Declare types

import { AnyComponent } from 'preact';

export type ExtractGeneric<Type> =
  Type extends AnyComponent<infer P> ? P : never;
