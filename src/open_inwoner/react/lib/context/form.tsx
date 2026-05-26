// import { computed, useSignal } from '@preact/signals';
// import isEqual from 'lodash/isEqual';
// import mapValues from 'lodash/mapValues';
// import xor from 'lodash/xor';
// import { type AnyComponent as AC } from 'preact';
// import { useRef } from 'preact/hooks';
// import {
//   FilterContext,
//   type FilterContextValue,
//   useFilterContext,
//   useRequiredFilterContext,
// } from '@react/components/Filter/context';
// import {
//   FormContext,
//   type FormContextValue,
//   type FormFieldBinding,
//   useFormContext,
//   useRequiredFormContext,
// } from '@react/components/Form/context';

// export type { FormContextValue, FormFieldBinding, FilterContextValue };
// export {
//   FormContext,
//   FilterContext,
//   useFormContext,
//   useRequiredFormContext,
//   useFilterContext,
//   useRequiredFilterContext,
// };

// /**
//  * Standalone FormContext provider for Storybook stories and unit tests.
//  *
//  * Provides the same field-value machinery as oip-form but without a `<form>`
//  * element, making it suitable for wrapping individual components in isolation.
//  * Does NOT provide FilterContext — use FormFilterProvider when you also need
//  * label registration and the submit action.
//  */
// const FormProvider: AC<{}> = ({ children }) => {
//   const values = useSignal<Record<string, string[]>>({});
//   const initial = useRef<Record<string, string[]>>({});
//   const bindings = useRef<Record<string, FormFieldBinding>>({});

//   const isDirty = computed(() => !isEqual(values.value, initial.current));
//   const isEmpty = computed(() =>
//     Object.values(values.value).every((v) => v.length === 0)
//   );

//   const register = (
//     name: string,
//     defaultValue?: string[]
//   ): FormFieldBinding => {
//     if (!bindings.current[name]) {
//       const def = defaultValue ?? [];
//       values.value = { ...values.value, [name]: def };
//       initial.current[name] = def;
//       bindings.current[name] = {
//         value: computed(() => values.value[name] ?? []),
//         setValue: (v: string[]) => {
//           values.value = { ...values.value, [name]: v };
//         },
//         onChange: (value: string, multiple: boolean) => {
//           const current = values.value[name] ?? [];
//           const next = multiple ? xor(current, [value]) : [value];
//           values.value = { ...values.value, [name]: next };
//         },
//       };
//     }
//     return bindings.current[name];
//   };

//   const removeValue = (fieldName: string, value: string): void => {
//     const current = values.value[fieldName] ?? [];
//     values.value = {
//       ...values.value,
//       [fieldName]: current.filter((v) => v !== value),
//     };
//   };

//   const toggle = (
//     fieldName: string,
//     value: string,
//     multiple: boolean
//   ): void => {
//     const current = values.value[fieldName] ?? [];
//     const next = multiple ? xor(current, [value]) : [value];
//     values.value = { ...values.value, [fieldName]: next };
//   };

//   const reset = (): void => {
//     values.value = mapValues(values.value, () => []);
//   };

//   const submit = (fn: (values: Record<string, string[]>) => void): void => {
//     fn(values.value);
//   };

//   return (
//     <FormContext.Provider
//       value={{
//         register,
//         values,
//         removeValue,
//         toggle,
//         isDirty,
//         isEmpty,
//         submit,
//         reset,
//       }}
//     >
//       {children}
//     </FormContext.Provider>
//   );
// };

// /**
//  * Standalone FilterContext provider for Storybook stories and unit tests.
//  *
//  * Provides label registration and a no-op submit action. Must be rendered
//  * inside a FormProvider (or oip-form) since it reads FormContext.
//  * Use FormFilterProvider for a single combined wrapper.
//  */
// const FilterProvider: AC<{}> = ({ children }) => {
//   const formCtx = useRequiredFormContext();
//   const optionLabels = useRef<Record<string, Record<string, string>>>({});

//   const registerLabel = (
//     fieldName: string,
//     value: string,
//     label: string
//   ): void => {
//     if (!optionLabels.current[fieldName]) {
//       optionLabels.current[fieldName] = {};
//     }
//     optionLabels.current[fieldName][value] = label;
//   };

//   const getLabel = (fieldName: string, value: string): string =>
//     optionLabels.current[fieldName]?.[value] ?? value;

//   const submit = (): void => {
//     formCtx.submit((values) => {
//       const params = new URLSearchParams();
//       Object.entries(values).forEach(([key, vals]) => {
//         vals.forEach((v) => params.append(key, v));
//       });
//       window.location.assign(`${window.location.pathname}?${params}`);
//     });
//   };

//   return (
//     <FilterContext.Provider value={{ registerLabel, getLabel, submit }}>
//       {children}
//     </FilterContext.Provider>
//   );
// };

// // /**
// //  * Combined FormContext + FilterContext provider for Storybook stories and unit tests.
// //  *
// //  * Wraps both FormProvider and FilterProvider so component trees that require
// //  * both contexts (oip-form-button, oip-filter-chips, oip-select) can be tested
// //  * with a single wrapper component.
// //  */
// // export const FormFilterProvider: AC<{}> = ({ children }) => (
// //   <FormProvider>
// //     <FilterProvider>{children}</FilterProvider>
// //   </FormProvider>
// // );
