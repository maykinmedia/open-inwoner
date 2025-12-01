import { ActionSingle } from '@gemeente-denhaag/action';
import { usePropsOrScriptData } from '@react/lib/json/getJsonScriptData';
import { WebComponentLoader } from '@react/lib/web-component';
import { FunctionComponent as FC } from 'preact';
import { WEB_COMPONENT_NAME } from '.';
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

const ActionList: FC<IActionListProps> = ({ actionsId, actions }) => {
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

export const loader = WebComponentLoader.loadWC(WEB_COMPONENT_NAME, ActionList);

export default ActionList;
