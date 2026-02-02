import { AnyComponent as AC } from 'preact';

export interface ITableBodyProps {
  children?: any;
}

// Role "rowgroup" is set via ElementInternals in web component registration
const TableBody: AC<ITableBodyProps> = ({ children }) => {
  return <>{children}</>;
};

export default TableBody;
