import { AnyComponent as AC } from 'preact';

export interface ITableHeaderProps {
  children?: any;
}

const TableHeader: AC<ITableHeaderProps> = ({ children }) => {
  return <thead class="utrecht-table__header">{children}</thead>;
};

export default TableHeader;
