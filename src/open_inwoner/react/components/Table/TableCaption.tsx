import { AnyComponent as AC } from 'preact';

export interface ITableCaptionProps {
  content?: string;
  children?: any;
}

// Role "caption" is set via ElementInternals in web component registration
const TableCaption: AC<ITableCaptionProps> = ({ content, children }) => {
  return <>{content || children}</>;
};

export default TableCaption;
