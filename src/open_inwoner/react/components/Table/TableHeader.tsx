import { AnyComponent as AC } from 'preact';

export interface ITableHeaderProps {
  children?: any;
}

// Role "rowgroup" is set via ElementInternals in web component registration
const TableHeader: AC<ITableHeaderProps> = ({ children }) => {
  return <>{children}</>;
};

export default TableHeader;
