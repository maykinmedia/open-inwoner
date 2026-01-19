import { ComponentChildren, RenderableProps } from 'preact';

export interface CardGridProps extends RenderableProps<{}> {
  columns?: 1 | 2 | 3 | 4;
  children?: ComponentChildren;
}
