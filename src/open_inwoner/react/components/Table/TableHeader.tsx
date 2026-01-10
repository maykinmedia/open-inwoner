import { AnyComponent as AC, ComponentChildren } from 'preact';

export interface ITableHeaderProps {
  children?: ComponentChildren;
}

const TableHeader: AC<ITableHeaderProps> = ({ children }) => {
  return <thead class="utrecht-table__header">{children}</thead>;
};

export default TableHeader;
