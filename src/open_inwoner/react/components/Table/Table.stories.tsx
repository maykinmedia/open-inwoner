import { Meta } from '@storybook/preact';
import Table from './Table';
import type { ITableProps } from './Table';
// import { TABLE_DEFINITION } from './constants';
// import { withLoader } from '@react/lib/decorators/storybook';

const meta: Meta<ITableProps> = {
  title: 'Components/Table',
  component: Table,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The Table component structures data in rows and columns. It can be used as a React component or as a web component.

**Features:**
- Table Caption for semantic HTML
- Optional Table Footer for totals or summary data
- Configurable columns with headers
- Multiple rows of data
- Built from @utrecht/component-library-react library and @utrecht/table-css styles

**Props:**
- \`tableId\`: Optional string - ID of a script tag containing JSON data for web component usage
- \`caption\`: Optional string - Title/label for the table
- \`columns\`: Optional array of objects with \`header\` (string) and \`key\` (string) properties
- \`rows\`: Optional array of objects where each key matches a column's \`key\` property
- \`footerRow\`: Optional object for footer data, uses same key structure as rows
- \`footerColSpan\`: Optional number or string - Column span for the first cell in the footer

**Web Component usage in HTML:**
\`\`\`
<script type="application/json" id="table-data">
{
  "caption": "My Table",
  "columns": [
    { "header": "Name", "key": "name" },
    { "header": "Value", "key": "value" }
  ],
  "rows": [
    { "name": "Item 1", "value": "100" }
  ],
  "footerRow": {
    "name": "Total",
    "value": "100"
  },
  "footerColSpan": 1
}
</script>
<utrecht-table table-id="table-data"></utrecht-table>
\`\`\`
        `,
      },
    },
  },
  argTypes: {
    // tableId: {
    //   control: 'text',
    //   description: 'ID of the script tag containing JSON table data',
    // },
    // caption: {
    //   control: 'text',
    //   description: 'Table caption',
    // },
    // columns: {
    //   control: 'object',
    //   description: 'Column definitions (header + key)',
    // },
    // rows: {
    //   control: 'object',
    //   description: 'Table rows (array of records)',
    // },
    // footerRow: {
    //   control: 'object',
    //   description: 'Optional footer row',
    // },
    // footerColSpan: {
    //   control: 'number',
    //   description: 'Optional column span for first footer cell',
    // },
  },
  tags: ['autodocs'],
};

export default meta;
// type Story = StoryObj<ITableProps>;
//
// const gftColumns = [
//   { header: 'Datum ophalen', key: 'date' },
//   { header: 'Tijd ophalen', key: 'time' },
//   { header: 'Gewicht (kg)', key: 'weight' },
// ];
//
// const gftRows = [
//   { date: 'vrijdag 14-11-2025', time: '11:07', weight: '17,0' },
//   { date: 'vrijdag 31-10-2025', time: '11:07', weight: '14,5' },
//   { date: 'vrijdag 17-10-2025', time: '11:07', weight: '20,0' },
//   { date: 'vrijdag 03-10-2025', time: '11:07', weight: '25,5' },
//   { date: 'vrijdag 19-09-2025', time: '11:07', weight: '18,5' },
// ];
//
// const gftFooter = {
//   date: 'Totaal gewicht',
//   time: '',
//   weight: '95,5',
// };

// export const Default: Story = {
//   args: {
//     caption:
//       'Groente, Fruit en Tuin afval (GFT) - Container 8701969 000000 00006 29 - 240 liter',
//     columns: gftColumns,
//     rows: gftRows,
//     footerRow: gftFooter,
//     footerColSpan: 2, // Span first 2 columns
//   },
// };
//
// export const Empty: Story = {
//   args: {
//     caption:
//       'Groente, Fruit en Tuin afval (GFT) - Container 8701969 000000 00006 29 - 240 liter',
//     columns: gftColumns,
//     rows: [],
//   },
// };
//
// /**
//  * Rendered using script data but still through the Preact Table component
//  */
// export const WithScriptData: Story = {
//   args: {
//     tableId: 'storybook-preact-script-table',
//   },
//   render: ({ tableId }) => {
//     const data = {
//       caption:
//         'Groente, Fruit en Tuin afval (GFT) - Container 8701969 000000 00006 29 - 240 liter',
//       columns: gftColumns,
//       rows: gftRows,
//       footerRow: gftFooter,
//       footerColSpan: 2,
//     };
//
//     return (
//       <>
//         <script type="application/json" id={tableId}>
//           {JSON.stringify(data)}
//         </script>
//         <Table tableId={tableId} />
//       </>
//     );
//   },
// };
//
// /**
//  * Rendered as webcomponent
//  */
// export const AsWebComponent: Story = {
//   args: { tableId: 'gft-table-data' },
//   decorators: withLoader(TABLE_DEFINITION.tagName),
//   render: ({ tableId }) => {
//     const data = {
//       caption:
//         'Groente, Fruit en Tuin afval (GFT) - Container 8701969 000000 00006 29 - 240 liter',
//       columns: gftColumns,
//       rows: gftRows,
//       footerRow: gftFooter,
//       footerColSpan: 2,
//     };
//
//     return (
//       <>
//         <script type="application/json" id={tableId}>
//           {JSON.stringify(data)}
//         </script>
//         <utrecht-table table-id={tableId} />
//       </>
//     );
//   },
// };
