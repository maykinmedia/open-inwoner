import { AnyComponent as AC } from 'preact';

export interface ITableBodyProps {
  children?: any;
}

const TableBody: AC<ITableBodyProps> = ({ children }) => {
  return <tbody class="utrecht-table__body">{children}</tbody>;
};

export default TableBody;
