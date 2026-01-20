import { FunctionalComponent } from 'preact';
import clsx from 'clsx';
import './Badge.scss';

export type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info';

export interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
}

export const Badge: FunctionalComponent<BadgeProps> = ({
  label,
  variant = 'default',
}) => {
  if (!label) {
    return null;
  }

  return (
    <span class={clsx('oip-badge', `oip-badge--${variant}`)}>{label}</span>
  );
};

export default Badge;
