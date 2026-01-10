import { AnyComponent as AC, ComponentChildren } from 'preact';

export interface ITableBodyProps {
  children?: ComponentChildren;
}

const TableBody: AC<ITableBodyProps> = ({ children }) => {
  return <tbody class="utrecht-table__body">{children}</tbody>;
};

export default TableBody;
