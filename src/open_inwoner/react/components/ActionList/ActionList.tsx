import { ActionSingle } from '@gemeente-denhaag/action';
import { usePropsOrScriptData } from '@react/lib/json';
import { AnyComponent as AC } from 'preact';
import './ActionList.scss';

export interface IActionProps {
  title: string;
  message: string;
  action_url: string;
}

export interface IActionListProps {
  actionsId?: string;
  actions?: IActionProps[];
}

const ActionList: AC<IActionListProps> = ({ actionsId, actions }) => {
  if (!actionsId && !actions) return <></>;

  const data = usePropsOrScriptData<IActionProps[]>(actions, actionsId);

  return data?.map(({ title, message, action_url: url }, index) => {
    return (
      <ActionSingle key={index} link={url}>
        <span className="denhaag-action__content--oip-message">
          {message} |{' '}
        </span>
        <span className="denhaag-action__content--oip-title">{title}</span>
      </ActionSingle>
    );
  });
};

export default ActionList;
