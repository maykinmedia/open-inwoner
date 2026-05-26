import { type AnyComponent as AC } from 'preact';

/**
 * HOC that guards a component behind a nullable context check.
 *
 * The returned component renders `null` silently while the context is absent
 * (e.g. during the async propagation window between a web component rendering
 * and its parent's context event firing), then renders the wrapped component
 * once the context arrives.
 *
 * Usage mirrors `memo` or `forwardRef` — wrap the component function directly,
 * no separate Inner component needed:
 *
 * @example
 * const MyComponent = withContextGuard(useMyNullableContext, (props) => {
 *   const ctx = useRequiredMyContext(); // safe — guard ensures it exists
 *   return <div>{ctx.value}</div>;
 * });
 *
 * @param useNullableHook - Hook that returns the context value or `null`.
 * @param Component       - Component to render once the context is available.
 */
export function withContextGuard<P extends {}>(
  useNullableHook: () => unknown | null,
  Component: AC<P>
): AC<P> {
  return (props) => {
    const ctx = useNullableHook();
    return ctx ? <Component {...props} /> : null;
  };
}
