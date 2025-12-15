import {
  TableContainer,
  Table as UtrechtTable,
  TableCaption,
  TableHeader,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  TableFooter,
} from '@utrecht/component-library-react/dist';
import { usePropsOrScriptData } from '@react/lib/json';
import { AnyComponent as AC } from 'preact';
import './Table.scss';

export interface ITableColumn {
  header: string;
  key: string;
  scope?: 'col' | 'colgroup' | 'row' | 'rowgroup'; // Optional scope, defaults to 'col'
}

export interface ITableRowProps {
  caption?: string;
  columns?: ITableColumn[];
  rows?: Array<Record<string, string>>;
  footerRow?: Record<string, string>;
  footerColSpan?: number;
  emptyStateMessage?: string; // Message when no data available
}

export interface ITableProps {
  jsonScriptId?: string;
  caption?: string;
  columns?: ITableColumn[];
  rows?: Array<Record<string, string>>;
  footerRow?: Record<string, string>;
  footerColSpan?: number;
  emptyStateMessage?: string; // Message when no data available
}

const Table: AC<ITableProps> = ({
  jsonScriptId,
  caption,
  columns,
  rows,
  footerRow,
  footerColSpan,
  emptyStateMessage,
}) => {
  if (!jsonScriptId && !rows) return <></>;

  const data = usePropsOrScriptData<ITableRowProps>(
    { caption, columns, rows, footerRow, footerColSpan, emptyStateMessage },
    jsonScriptId
  );

  if (!data?.columns) return <></>;

  // Convert footerColSpan to number and trim accidental whitespace (it comes as string from JSON)
  const colSpanValue = data.footerColSpan || 1;

  const isEmpty = !data.rows || data.rows.length === 0;

  return (
    <TableContainer>
      <UtrechtTable>
        <TableCaption>{data.caption}</TableCaption>

        <TableHeader>
          <TableRow>
            {/* LOOP 1: Iterate over each column to render table headers */}
            {data.columns?.map(({ header, scope = 'col' }, index) => (
              <TableHeaderCell key={index} scope={scope}>
                {header}
              </TableHeaderCell>
            ))}
          </TableRow>
        </TableHeader>

        <TableBody>
          {/* If empty, show a single row with the empty state message */}
          {isEmpty ? (
            <TableRow>
              <TableCell colSpan={data.columns?.length || 1}>
                {data.emptyStateMessage}
              </TableCell>
            </TableRow>
          ) : (
            /* LOOP 2 (OUTER): Iterate over each row of data */
            data.rows!.map((row, rowIndex) => (
              <TableRow key={rowIndex}>
                {/* LOOP 3 (INNER): For each row, iterate over each column to render cells */}
                {data.columns?.map(({ key }, colIndex) => (
                  <TableCell key={`${rowIndex}-${colIndex}`}>
                    {/* Extract the value for this cell using the column key */}
                    {row[key]}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>

        {/* FOOTER: Optional footer row (totals, summary, etc.) with colspan support */}
        {data.footerRow && (
          <TableFooter>
            <TableRow>
              {/* LOOP 4: Iterate over columns for footer cells */}
              {data.columns?.map(({ key }, colIndex) => {
                // Skip cells that are covered by the colspan
                if (colIndex > 0 && colIndex < colSpanValue) {
                  return null;
                }

                return (
                  <TableCell
                    key={`footer-${colIndex}`}
                    colSpan={colIndex === 0 ? colSpanValue : undefined}
                  >
                    {data.footerRow?.[key]}
                  </TableCell>
                );
              })}
            </TableRow>
          </TableFooter>
        )}
      </UtrechtTable>
    </TableContainer>
  );
};

export default Table;
