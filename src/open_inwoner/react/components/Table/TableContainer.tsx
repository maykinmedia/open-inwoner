import { AnyComponent as AC, ComponentChildren } from 'preact';
import './Table.scss';

export interface ITableContainerProps {
  children?: ComponentChildren;
}

const TableContainer: AC<ITableContainerProps> = ({ children }) => {
  return <div class="utrecht-table-container">{children}</div>;
};

export default TableContainer;
