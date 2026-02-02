import { AnyComponent as AC } from 'preact';

export interface ITableRowProps {
  children?: any;
}

// Role "row" is set via ElementInternals in web component registration
const TableRow: AC<ITableRowProps> = ({ children }) => {
  return <>{children}</>;
};

export default TableRow;
