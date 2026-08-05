import clsx from 'clsx';
import kebabCase from 'lodash/kebabCase';
import { AnyComponent as AC } from 'preact';
import { Paragraph } from '../Paragraph';
import { MaterialIcon } from '../MaterialIcon';
import './HomePluginCard.scss';
import type { HomepageCardTypes } from './types';

const HomePluginCard: AC<HomepageCardTypes> = ({
  title,
  description,
  identificatie,
  detailUrl,
  date,
  address,
  renderAsHeading = false,
}) => {
  const Heading = String(renderAsHeading) !== 'false' ? 'h3' : 'p';
  const addressLineFirst = title && date && address;
  const id = 'card-' + kebabCase(identificatie);
  // Some cases (e.g. a formulier without a `vervolg_link`) have no
  // destination to link to. Rendering an empty `href` would make the
  // browser navigate to the current page, which is worse than not being
  // clickable at all, so we render a non-interactive card instead.
  const Container = detailUrl ? 'a' : 'div';
  const content = (
    <div class="oip-home-plugin-card__content">
      <div class="oip-home-plugin-card__body">
        <Heading
          id={!addressLineFirst ? id : undefined}
          class={clsx({
            ['utrecht-heading-2']: !addressLineFirst,
            ['nl-paragraph']: addressLineFirst,
          })}
        >
          {addressLineFirst ? (
            <>
              {date && <span>{date}</span>}
              {address && <span>{address}</span>}
            </>
          ) : (
            title
          )}
        </Heading>
        <Paragraph id={addressLineFirst ? id : undefined}>
          {addressLineFirst ? title : description}
        </Paragraph>
      </div>

      {detailUrl && <MaterialIcon name="arrow_forward" />}
    </div>
  );
  return (
    <Container
      {...(detailUrl ? { href: detailUrl } : {})}
      class="oip-home-plugin-card"
      aria-labelledby={id}
    >
      {content}
    </Container>
  );
};

export default HomePluginCard;
