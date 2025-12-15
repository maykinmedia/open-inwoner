import { AnyComponent as AC } from 'preact';
import './Table.scss';

export interface ITableContainerProps {
  children?: any;
}

const TableContainer: AC<ITableContainerProps> = ({ children }) => {
  return <div class="utrecht-table-container">{children}</div>;
};

export default TableContainer;
