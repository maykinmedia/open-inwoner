import clsx from 'clsx';
import kebabCase from 'lodash/kebabCase';
import { AnyComponent as AC } from 'preact';
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
  return (
    <a href={detailUrl} class="oip-home-plugin-card" aria-labelledby={id}>
      <div class="oip-home-plugin-card__content">
        <div class="oip-home-plugin-card__body">
          <Heading
            id={!addressLineFirst ? id : undefined}
            class={clsx({
              ['utrecht-heading-2']: !addressLineFirst,
              ['utrecht-paragraph']: addressLineFirst,
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
          <p
            class={clsx('utrecht-paragraph', 'utrecht-paragraph-muted')}
            id={addressLineFirst ? id : undefined}
          >
            {addressLineFirst ? title : description}
          </p>
        </div>

        <MaterialIcon name="east" />
      </div>
    </a>
  );
};

export default HomePluginCard;
