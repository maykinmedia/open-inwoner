import { ComponentChildren, AnyComponent as FC } from 'preact';
import './HomepagePluginSection.scss';

export interface IHomepagePluginSectionProps {
  title?: string;
  nextUrl?: string;
  nextUrlLabel?: string;
  showIndicator?: boolean;
  columns: number;
  children: ComponentChildren;
}

const HomepagePluginSection: FC<IHomepagePluginSectionProps> = ({
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
            <h2 class={`utrecht-heading-2 ${showIndicator ? 'indicator' : ''}`}>
              {title}
            </h2>
            {showIndicator && (
              <span
                aria-hidden="true"
                class="material-icons plugin__notification-indicator"
              >
                fiber_manual_record
              </span>
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
            <span aria-hidden="true" class="material-icons">
              arrow_forward
            </span>
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

export default HomepagePluginSection;
