import { AnyComponent as AC, ComponentChildren } from 'preact';

export interface ITableFooterProps {
  children?: ComponentChildren;
}

const TableFooter: AC<ITableFooterProps> = ({ children }) => {
  return <tfoot class="utrecht-table__footer">{children}</tfoot>;
};

export default TableFooter;
