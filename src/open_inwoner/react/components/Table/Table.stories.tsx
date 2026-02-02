import type { Meta, StoryObj } from '@storybook/preact-vite';
import type { ITableProps } from './Table';
import Table from './Table';
import TableCaption from './TableCaption';
import TableHeader from './TableHeader';
import TableHeaderCell from './TableHeaderCell';
import TableBody from './TableBody';
import TableRow from './TableRow';
import TableCell from './TableCell';
import TableFooter from './TableFooter';
import TableContainer from './TableContainer';
import { WebComponentLoader } from '@react/lib/web-component';

const meta: Meta<ITableProps> = {
  title: 'Components/Table',
  component: Table,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The Table component uses ElementInternals to set ARIA roles on custom elements.
Each component renders only its children - the semantic roles are applied via \`attachInternals()\`.

**Component Structure:**
- \`<oip-table>\` → role="table"
- \`<oip-table-caption>\` → role="caption"
- \`<oip-table-header>\` → role="rowgroup"
- \`<oip-table-header-cell>\` → role="columnheader"
- \`<oip-table-body>\` → role="rowgroup"
- \`<oip-table-row>\` → role="row"
- \`<oip-table-cell>\` → role="cell"
- \`<oip-table-footer>\` → role="rowgroup"
        `,
      },
    },
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<ITableProps>;

/**
 * Basic table with header, body, and data rows.
 * Each component just renders children - roles are set via ElementInternals.
 */
export const Default: Story = {
  render: () => (
    <TableContainer>
      <Table>
        <TableCaption>
          Groente, Fruit en Tuin afval (GFT) - Container 240 liter
        </TableCaption>
        <TableHeader>
          <TableRow>
            <TableHeaderCell>Datum ophalen</TableHeaderCell>
            <TableHeaderCell>Tijd ophalen</TableHeaderCell>
            <TableHeaderCell>Gewicht (kg)</TableHeaderCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>vrijdag 14-11-2025</TableCell>
            <TableCell>11:07</TableCell>
            <TableCell>17,0</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>vrijdag 31-10-2025</TableCell>
            <TableCell>11:07</TableCell>
            <TableCell>14,5</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>vrijdag 17-10-2025</TableCell>
            <TableCell>11:07</TableCell>
            <TableCell>20,0</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  ),
};

/**
 * Table with a footer row for totals.
 */
export const WithFooter: Story = {
  render: () => (
    <TableContainer>
      <Table>
        <TableCaption>GFT Container - Met totaal</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHeaderCell>Datum</TableHeaderCell>
            <TableHeaderCell>Gewicht (kg)</TableHeaderCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>14-11-2025</TableCell>
            <TableCell>17,0</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>31-10-2025</TableCell>
            <TableCell>14,5</TableCell>
          </TableRow>
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell>Totaal</TableCell>
            <TableCell>31,5</TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    </TableContainer>
  ),
};

/**
 * Simple table without caption.
 */
export const Simple: Story = {
  render: () => (
    <TableContainer>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHeaderCell>Name</TableHeaderCell>
            <TableHeaderCell>Value</TableHeaderCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Item 1</TableCell>
            <TableCell>100</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Item 2</TableCell>
            <TableCell>200</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  ),
};

/**
 * Table rendered as web components with ElementInternals.
 * Each custom element has its ARIA role set via attachInternals().
 */
export const AsWebComponent: Story = {
  loaders: [
    async () => {
      await Promise.all([
        WebComponentLoader.importWebComponent('oip-table-container'),
        WebComponentLoader.importWebComponent('oip-table'),
        WebComponentLoader.importWebComponent('oip-table-caption'),
        WebComponentLoader.importWebComponent('oip-table-header'),
        WebComponentLoader.importWebComponent('oip-table-header-cell'),
        WebComponentLoader.importWebComponent('oip-table-body'),
        WebComponentLoader.importWebComponent('oip-table-row'),
        WebComponentLoader.importWebComponent('oip-table-cell'),
        WebComponentLoader.importWebComponent('oip-table-footer'),
      ]);
    },
  ],
  render: () => (
    <div
      dangerouslySetInnerHTML={{
        __html: `
          <oip-table-container>
            <oip-table is="table">
              <oip-table-caption>GFT Container - Web Components</oip-table-caption>
              <oip-table-header role="row-group">
                <oip-table-row is="tr" role="row">
                  <oip-table-header-cell>Datum</oip-table-header-cell>
                  <oip-table-header-cell>Tijd</oip-table-header-cell>
                  <oip-table-header-cell>Gewicht (kg)</oip-table-header-cell>
                </oip-table-row>
              </oip-table-header>
              <oip-table-body>
                <oip-table-row>
                  <oip-table-cell>14-11-2025</oip-table-cell>
                  <oip-table-cell>11:07</oip-table-cell>
                  <oip-table-cell>17,0</oip-table-cell>
                </oip-table-row>
                <oip-table-row>
                  <oip-table-cell>31-10-2025</oip-table-cell>
                  <oip-table-cell>11:07</oip-table-cell>
                  <oip-table-cell>14,5</oip-table-cell>
                </oip-table-row>
              </oip-table-body>
              <oip-table-footer>
                <oip-table-row>
                  <oip-table-cell>Totaal</oip-table-cell>
                  <oip-table-cell></oip-table-cell>
                  <oip-table-cell>31,5</oip-table-cell>
                </oip-table-row>
              </oip-table-footer>
            </oip-table>
          </oip-table-container>
        `,
      }}
    />
  ),
};
