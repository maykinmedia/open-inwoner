import { AnyComponent as AC, ComponentChildren } from 'preact';

export interface ITableProps {
  caption?: string;
  children?: ComponentChildren;
}

const Table: AC<ITableProps> = ({ caption, children }) => {
  return (
    <table class="utrecht-table">
      {caption && <caption class="utrecht-table__caption">{caption}</caption>}
      {children}
    </table>
  );
};

export default Table;
