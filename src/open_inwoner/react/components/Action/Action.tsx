import { ActionSingle } from '@gemeente-denhaag/action';
import { StatusBadge } from '@utrecht/component-library-react';
import { AnyComponent as AC } from 'preact';
import './Action.scss';

export type ActionStatus = 'info' | 'warning' | 'failure' | 'success';

const STATUSES: ActionStatus[] = ['info', 'warning', 'failure', 'success'];

const toStatus = (value?: string): ActionStatus =>
  STATUSES.includes(value as ActionStatus) ? (value as ActionStatus) : 'info';

const BADGE_STATUS: Record<ActionStatus, string | undefined> = {
  info: undefined,
  warning: 'warning',
  failure: 'danger',
  success: 'success',
};

export interface IActionProps {
  message: string;
  actionUrl: string;
  label?: string;
  status?: string;
}

const Action: AC<IActionProps> = ({ actionUrl, message, label, status }) => {
  const badge = label ? (
    <StatusBadge status={BADGE_STATUS[toStatus(status)]}>{label}</StatusBadge>
  ) : undefined;

  return (
    <ActionSingle link={actionUrl} details={badge}>
      <span className="denhaag-action__content--oip-message">{message}</span>
    </ActionSingle>
  );
};

export default Action;
