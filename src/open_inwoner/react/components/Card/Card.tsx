import { ComponentChildren, FunctionalComponent } from 'preact';
import clsx from 'clsx';
import { Badge, BadgeVariant } from '../Badge';
import './Card.scss';

export interface CardProps {
  href?: string;
  variant?: 'default' | 'location' | 'category' | 'product';
  className?: string;
  children: ComponentChildren;
}

export const Card = ({
  href,
  variant = 'default',
  className,
  children,
}: CardProps) => {
  const cardClasses = clsx('card', variant && `card--${variant}`, className);

  if (href) {
    return (
      <a href={href} class={cardClasses}>
        {children}
      </a>
    );
  }

  return <div class={cardClasses}>{children}</div>;
};

export interface CardBodyProps {
  className?: string;
  children: ComponentChildren;
}

export const CardBody = ({ className, children }: CardBodyProps) => (
  <div class={clsx('card__body', className)}>{children}</div>
);

export interface CardHeadingProps {
  href?: string;
  level?: 2 | 3;
  children: ComponentChildren;
}

export const CardHeading = ({
  href,
  level = 3,
  children,
}: CardHeadingProps) => {
  const Tag = `h${level}` as const;
  const headingClass = clsx(
    `utrecht-heading-${level}`,
    `card__heading-${level}`
  );

  return (
    <Tag class={headingClass}>
      {href ? (
        <a href={href} class="card__heading-link">
          {children}
        </a>
      ) : (
        children
      )}
    </Tag>
  );
};

export interface CardContentProps {
  className?: string;
  children: ComponentChildren;
}

export const CardContent = ({ className, children }: CardContentProps) => (
  <div class={clsx('card__content', className)}>{children}</div>
);

// Base card props for web component usage
export interface BaseCardProps {
  title?: string;
  description?: string;
  subtitle?: string;
  status?: string;
  href?: string;
  badgeLabel?: string;
  badgeVariant?: BadgeVariant;
  footer?: string;
}

export const BaseCard = ({
  title,
  description,
  subtitle,
  status,
  href,
  badgeLabel,
  badgeVariant,
  footer,
}: BaseCardProps) => {
  if (!title && !description && !subtitle) {
    return null;
  }

  return (
    <Card href={href}>
      <CardBody>
        <div class="card__header">
          {title && <CardHeading level={3}>{title}</CardHeading>}
          {badgeLabel && <Badge label={badgeLabel} variant={badgeVariant} />}
        </div>
        {description && <p class="utrecht-paragraph">{description}</p>}
        {(subtitle || status) && (
          <div class="card__details">
            {subtitle && <p class="utrecht-paragraph">{subtitle}</p>}
            {status && <p class="utrecht-paragraph">{status}</p>}
          </div>
        )}
        {footer && (
          <div class="card__footer">
            <span class="card__footer-text">{footer}</span>
            <span class="material-icons-outlined">arrow_forward</span>
          </div>
        )}
      </CardBody>
    </Card>
  );
};

// LocationCard specific types and component
export interface LocationCardProps {
  locationName?: string;
  locationUrl?: string;
  addressLine1?: string;
  addressLine2?: string;
  phoneNumber?: string;
  email?: string;
}

export const LocationCard = ({
  locationName,
  locationUrl,
  addressLine1,
  addressLine2,
  phoneNumber,
  email,
}: LocationCardProps) => {
  const hasContent =
    locationName || addressLine1 || addressLine2 || phoneNumber || email;

  if (!hasContent) {
    return null;
  }

  return (
    <Card variant="location">
      <CardBody>
        {locationName && (
          <CardHeading href={locationUrl} level={3}>
            {locationName}
          </CardHeading>
        )}
        <div class="card__contact-info">
          {addressLine1 && <p class="utrecht-paragraph">{addressLine1}</p>}
          {addressLine2 && <p class="utrecht-paragraph">{addressLine2}</p>}
          {phoneNumber && (
            <a href={`tel:${phoneNumber}`} class="link link--secondary">
              {phoneNumber}
            </a>
          )}
          {email && (
            <a
              href={`mailto:${email}`}
              class="link link--secondary link--mailto"
            >
              {email}
            </a>
          )}
        </div>
      </CardBody>
    </Card>
  );
};

// Union type for all card variants props
export type OipCardProps = {
  variant?: 'default' | 'location' | 'category' | 'product';
} & BaseCardProps &
  LocationCardProps;

export type { BadgeVariant };

/**
 * OipCard - Web component entry point
 * Renders different card types based on the variant prop
 */
const OipCard: FunctionalComponent<OipCardProps> = ({
  variant = 'default',
  ...props
}) => {
  switch (variant) {
    case 'location':
      return <LocationCard {...props} />;
    default:
      return <BaseCard {...props} />;
  }
};

export default OipCard;
