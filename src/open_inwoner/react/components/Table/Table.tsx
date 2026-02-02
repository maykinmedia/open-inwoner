import { AnyComponent as AC } from 'preact';

export interface ITableProps {
  caption?: string;
  children?: any;
}

// Role "table" is set via ElementInternals in web component registration
const Table: AC<ITableProps> = ({ children }) => {
  return <>{children}</>;
};

export default Table;
