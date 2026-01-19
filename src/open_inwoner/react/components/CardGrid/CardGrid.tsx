import { ComponentChildren, AnyComponent as AC, RenderableProps } from 'preact';
import './CardGrid.scss';

export type CardGridProps = RenderableProps<{
  columns?: 1 | 2 | 3 | 4;
  children?: ComponentChildren;
}>;

const CardGrid: AC<CardGridProps> = ({ columns = 2, children }) => {
  return (
    <section class="card-grid">
      <div class="card__content">
        <div class={`card-container card-container--columns-${columns}`}>
          {children}
        </div>
      </div>
    </section>
  );
};

export default CardGrid;
