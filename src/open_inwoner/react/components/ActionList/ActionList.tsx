import { AnyComponent as AC } from 'preact';
import './ActionList.scss';

export interface IActionListProps {}

/**
 * ActionList is just a wrapper for `oip-action` components
 */
const ActionList: AC<IActionListProps> = () => {
  return <slot />;
};

export default ActionList;
