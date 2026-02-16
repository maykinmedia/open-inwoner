import { withLoader } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact';
import File from './File';
import { FILE_ITEM_DEFINITION } from './constants';
import 'material-icons/iconfont/material-icons.css';
import '@gemeente-denhaag/file/index.css';
import type { IFileProps } from './File';

type Story = StoryObj<IFileProps>;

const meta: Meta<typeof File> = {
  title: 'Components/File',
  component: File,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `A file displays a link to download an attachment and shows metadata about the file.

## NL Design-System
We are inheriting the CSS styles and CSS tokens from the Den Haag React File component, but since Open Inwoner has its own logic of handling the type of icon to show depending on extension we are overriding some of the structure. Also we cannot have anchors inside anchors so the File-item is a Div instead of a surrounding anchor.

## When to use
A file is used to present and download a file that is uploaded by the user or an employee.

## Anatomy
The file consists of:
1. **File name** - the required name of the file
2. **Preview** - shows an icon of the type of the file (e.g. document, image)
3. **Navigational link** - shows the download option or delete button
4. **Container**

## File Types
Icons are determined by file extension or isImage flag:
- Images: jpg, jpeg, png, gif, webp, tiff, tif, svg, pdf → image icon
- All other types → document icon

## Interactive states
The file contains the states normal, hover, and focus.

## Accessibility
In order to comply with accessibility standards you should not force a file to open in a new tab. It must be left up to the user to decide whether to download a file, or open in a new tab.

## Best practices

Files download should:
- Be used for all downloads.
- Include file size and type. Showing the file size is particularly nice for users that are on reduced data allowances (i.e. mobile), and also offers an indication on how long a file might take to download.
- Show delete button only when appropriate with confirmation dialog.
`,
      },
    },
  },
  decorators: [
    (Story) => (
      <div style={{ width: '800px' }}>
        <Story />
      </div>
    ),
  ],
  tags: ['autodocs'],
};

export default meta;

export const Default: Story = {
  args: {
    name: 'document.pdf',
    href: '/download/123',
    size: '2000',
    extension: 'pdf',
  },
};

export const SingleFile: Story = {
  args: {
    name: 'document.pdf',
    href: '/download/123',
    size: '2000',
    extension: 'pdf',
  },
};

export const ImageFile: Story = {
  args: {
    name: 'photo.jpg',
    href: '/download/456',
    size: '5000',
    extension: 'jpg',
    isImage: true,
  },
};

export const WithDelete: Story = {
  args: {
    name: 'document.pdf',
    href: '/download/123',
    size: '2000',
    extension: 'pdf',
    showDelete: true,
    removableLabel: 'Verwijderen',
    deleteUrl: '/delete/123',
  },
};

export const WithDenHaagMetadata: Story = {
  args: {
    name: 'presentation.pdf',
    href: '/download/999',
    size: '3500',
    extension: 'pdf',
    lastUpdated: 'Laatst bijgewerkt: 9 januari',
  },
};

// ============================================
// Web Component
// ============================================

export const AsWebComponent: Story = {
  name: 'As Web Component',
  args: {
    name: 'document.pdf',
    href: '/download/123',
    size: '2000',
    extension: 'pdf',
  },
  decorators: [withLoader(FILE_ITEM_DEFINITION.tagName)],
  render: ({ name, href, size, extension }: any) => (
    <file-denhaag name={name} href={href} size={size} extension={extension} />
  ),
};
