import { AnyComponent as AC } from 'preact';

export interface ITableHeaderCellProps {
  content?: string;
  scope?: 'col' | 'row';
  children?: any;
}

// Role "columnheader" or "rowheader" is set via ElementInternals in web component registration
const TableHeaderCell: AC<ITableHeaderCellProps> = ({ content, children }) => {
  return <>{content || children}</>;
};

export default TableHeaderCell;
