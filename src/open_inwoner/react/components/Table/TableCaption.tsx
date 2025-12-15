import { AnyComponent as AC } from 'preact';

export interface ITableCaptionProps {
  content?: string; // not available in NLDS
  children?: any;
}

const TableCaption: AC<ITableCaptionProps> = ({ content, children }) => {
  return (
    <caption class="utrecht-table__caption">{content || children}</caption>
  );
};

export default TableCaption;
