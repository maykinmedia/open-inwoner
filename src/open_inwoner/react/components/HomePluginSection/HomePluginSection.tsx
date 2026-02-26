import { ComponentChildren, AnyComponent as AC, RenderableProps } from 'preact';
import { MaterialIcon } from '../MaterialIcon';
import './HomePluginSection.scss';

export type IHomePluginSectionProps = RenderableProps<{
  title?: string;
  nextUrl?: string;
  nextUrlLabel?: string;
  showIndicator?: boolean;
  columns: number;
  children?: ComponentChildren;
}>;

const HomePluginSection: AC<IHomePluginSectionProps> = ({
  title = '',
  nextUrl = '',
  nextUrlLabel = '',
  showIndicator = false,
  columns = 2,
  children,
}) => {
  return (
    <section class="plugin">
      <header class="plugin__header">
        {title && (
          <div class={showIndicator ? 'heading-2__indicator' : ''}>
            <h2
              class={`nl-heading--level-2 ${showIndicator ? 'indicator' : ''}`}
            >
              {title}
            </h2>
            {showIndicator && (
              <MaterialIcon
                name="fiber_manual_record"
                outlined={false}
                extraClassName={['plugin__notification-indicator']}
              />
            )}
          </div>
        )}
        {nextUrl && (
          <a
            class="button button--textless button--icon button--icon-after"
            href={nextUrl}
            title={nextUrlLabel}
            aria-label={nextUrlLabel}
          >
            <MaterialIcon name="arrow_forward" outlined={false} />
            {nextUrlLabel}
          </a>
        )}
      </header>
      <div class="plugin__grid" style={`--plugin-columns: ${columns}`}>
        {children}
      </div>
    </section>
  );
};

export default HomePluginSection;
