import clsx from 'clsx';
import kebabCase from 'lodash/kebabCase';
import { AnyComponent as AC } from 'preact';
import { MaterialIcon } from '../MaterialIcon';
import './CardTile.scss';
import type { CardTileTypes } from './types';

const CardTile: AC<CardTileTypes> = ({
  title,
  description,
  identificatie,
  detailUrl,
  date,
  address,
  keywords,
  code,
  createdDate,
  updatedDate,
  gepubliceerd,
  publicatieStartDatum,
  toegestaneStatussen,
  prijs,
  renderAsHeading = false,
}) => {
  const Heading = String(renderAsHeading) !== 'false' ? 'h3' : 'p';
  const isAddressLayout = title && date && address;
  const id = 'card-' + kebabCase(identificatie);

  // Handle keywords - convert string to array if needed
  const keywordsArray =
    typeof keywords === 'string'
      ? keywords
          .split(',')
          .map((k) => k.trim())
          .filter(Boolean)
      : Array.isArray(keywords)
        ? keywords
        : [];

  // Handle toegestaneStatussen - convert string to array if needed
  const statussenArray =
    typeof toegestaneStatussen === 'string'
      ? toegestaneStatussen
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean)
      : Array.isArray(toegestaneStatussen)
        ? toegestaneStatussen
        : [];

  return (
    <a
      href={detailUrl}
      class="card card__description-card"
      aria-labelledby={id}
    >
      <div class="card__body card__body--tabled">
        <Heading
          id={!isAddressLayout ? id : undefined}
          class={clsx('card__heading-2', {
            ['utrecht-heading-2']: !isAddressLayout,
            ['utrecht-paragraph']: isAddressLayout,
          })}
        >
          {isAddressLayout ? (
            <>
              {date && <span>{date}</span>}
              {address && <span>{address}</span>}
            </>
          ) : (
            title
          )}
        </Heading>

        {description && (
          <p
            class={clsx('utrecht-paragraph', 'utrecht-paragraph--muted')}
            id={isAddressLayout ? id : undefined}
          >
            {description}
          </p>
        )}

        {code && (
          <p class="utrecht-paragraph">
            <strong>Code:</strong> {code}
          </p>
        )}

        {prijs && (
          <p class="utrecht-paragraph">
            <strong>Prijs:</strong> € {prijs}
          </p>
        )}

        {keywordsArray.length > 0 && (
          <p class="utrecht-paragraph">
            <strong>Keywords:</strong> {keywordsArray.join(', ')}
          </p>
        )}

        {statussenArray.length > 0 && (
          <p class="utrecht-paragraph">
            <strong>Statussen:</strong> {statussenArray.join(', ')}
          </p>
        )}

        {(createdDate ||
          updatedDate ||
          gepubliceerd !== undefined ||
          publicatieStartDatum) && (
          <div class="card__tabled">
            {gepubliceerd !== undefined && (
              <>
                <div>
                  <strong>Gepubliceerd:</strong>
                </div>
                <div>{gepubliceerd ? 'Ja' : 'Nee'}</div>
              </>
            )}
            {publicatieStartDatum && (
              <>
                <div>
                  <strong>Publicatie start:</strong>
                </div>
                <div>{publicatieStartDatum}</div>
              </>
            )}
            {createdDate && (
              <>
                <div>
                  <strong>Aanmaak datum:</strong>
                </div>
                <div>{createdDate}</div>
              </>
            )}
            {updatedDate && (
              <>
                <div>
                  <strong>Update datum:</strong>
                </div>
                <div>{updatedDate}</div>
              </>
            )}
          </div>
        )}

        <span class="spacer"></span>
        <span class="button button--icon-before button--transparent button--primary">
          <MaterialIcon name="arrow_forward" />
        </span>
      </div>
    </a>
  );
};

export default CardTile;
