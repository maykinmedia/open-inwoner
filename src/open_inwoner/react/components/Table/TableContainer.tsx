import { AnyComponent as AC } from 'preact';
import './Table.scss';

export interface ITableContainerProps {
  children?: any;
}

// Container for table - no specific role needed
const TableContainer: AC<ITableContainerProps> = ({ children }) => {
  return <>{children}</>;
};

export default TableContainer;
