import { AnyComponent as AC } from 'preact';

export interface ITableFooterProps {
  children?: any;
}

// Role "rowgroup" is set via ElementInternals in web component registration
const TableFooter: AC<ITableFooterProps> = ({ children }) => {
  return <>{children}</>;
};

export default TableFooter;
