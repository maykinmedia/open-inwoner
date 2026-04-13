import { ActionSingle } from '@gemeente-denhaag/action';
import { AnyComponent as AC } from 'preact';
import './Action.scss';

export interface IActionProps {
  title: string;
  message: string;
  actionUrl: string;
}

const Action: AC<IActionProps> = ({ actionUrl, message, title }) => {
  return (
    <ActionSingle link={actionUrl}>
      <span className="denhaag-action__content--oip-message">{message} | </span>
      <span className="denhaag-action__content--oip-title">{title}</span>
    </ActionSingle>
  );
};

export default Action;
