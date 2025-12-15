import { AnyComponent as AC } from 'preact';

export interface ITableFooterProps {
  children?: any;
}

const TableFooter: AC<ITableFooterProps> = ({ children }) => {
  return <tfoot class="utrecht-table__footer">{children}</tfoot>;
};

export default TableFooter;
