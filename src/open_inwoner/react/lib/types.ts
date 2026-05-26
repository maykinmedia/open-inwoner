import { AnyComponent as AC } from 'preact';

export type ExtractGeneric<Type> = Type extends AC<infer P> ? P : never;
