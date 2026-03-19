import { withLoader } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact';
import File from './File';
import { FILE_ITEM_DEFINITION } from './constants';
import 'material-icons/iconfont/material-icons.css';
import '@gemeente-denhaag/file/index.css';
import type { IFileProps } from './File';

type Story = StoryObj<IFileProps>;

/** Helper to convert KB to bytes string for size prop to make stories more readable */
const kbToBytes = (kilobytes: number) => String(kilobytes * 1024);

const meta: Meta<typeof File> = {
  title: 'Components/File',
  component: File,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `A file displays a link to download an attachment and shows metadata about the file.

## NL Design-System
We are inheriting the CSS styles and CSS tokens from the Den Haag React File component, but since Open Inwoner has its own logic of handling the type of icon to show depending on extension we are overriding some of the structure. Also we cannot have anchors inside anchors so the File-item is a Div instead of one anchor surrounding everything.
For accessibility reasons we prefer not to make the entire File bar a link, so that screen readers will have more distinction in what is being read, and the download interaction or delete interaction become more clear.

## When to use
A file is used to present and download a file that is uploaded by the user or an employee.

## Anatomy
The file consists of:
1. **File name** - the required name of the file
2. **Preview icon** - shows an icon of the type of the file (e.g. document, image)
3. **Action** - optionally shows a download link or delete button, or none
4. **Extension** - shows the parsed extension in uppercase
5. **File size** - shows the file size in human readable form
6. **Container**

## File Types
Icons are determined by file extension or isImage flag:
- Images: jpg, jpeg, png, gif, webp, tiff, tif, svg... → image icon
- All other types → document icon

## Accessibility
In order to comply with accessibility standards you should not force a file to open in a new tab. It must be left up to the user to decide whether to download a file, or open in a new tab.

## Best practices

Files download should:
- Be used for all downloads.
- Always include file size and type. File size is especially helpful for users on limited data plans (e.g. mobile), and gives an indication of download time.
- Not wrap the entire file bar in a link. Instead, only the download or delete action is interactive, so screen readers can distinguish between the file metadata and the action.
- Only show the delete button when the user has permission to delete, always with a confirmation dialog before proceeding.
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
    downloadUrl: '/download/123',
    size: kbToBytes(2000),
    extension: 'pdf',
  },
};

export const ImageFile: Story = {
  args: {
    name: 'photo.jpg',
    downloadUrl: '/download/456',
    size: kbToBytes(5000),
    extension: 'jpg',
    isImage: true,
  },
};

export const WithDelete: Story = {
  args: {
    name: 'document.pdf',
    downloadUrl: '/download/123',
    size: kbToBytes(2000),
    extension: 'pdf',
    showDelete: true,
    removableLabel: 'Verwijderen',
    deleteUrl: '/delete/123',
  },
};

export const WithoutDeleteOrLink: Story = {
  args: {
    name: 'preview-samenwerking.doc',
    size: kbToBytes(123),
    extension: 'doc',
  },
  parameters: {
    docs: {
      description: {
        story:
          'When no `downloadUrl` or `deleteUrl` is provided, the file is displayed without any action. Useful for situations where the file is shown as preview only.',
      },
    },
  },
};

export const WithDenHaagMetadata: Story = {
  args: {
    name: 'presentation.pdf',
    downloadUrl: '/download/999',
    size: kbToBytes(3500),
    extension: 'pdf',
    lastUpdated: 'Laatst bijgewerkt: 9 januari',
  },
};

export const ExtensionParsedFromName: Story = {
  name: 'Extension parsed from filename',
  args: {
    name: 'photo.png',
    downloadUrl: '/download/789',
    size: kbToBytes(185),
  },
  parameters: {
    docs: {
      description: {
        story:
          'When no `extension` prop is provided, the extension is parsed from the filename. The correct image icon is shown automatically.',
      },
    },
  },
};

export const LargeFile: Story = {
  name: 'Large file (MB)',
  args: {
    name: 'archive.zip',
    downloadUrl: '/download/999',
    size: kbToBytes(2048),
    extension: 'zip',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Files larger than 1 MB are displayed in MB. Size is formatted automatically by the formatFileSize utility.',
      },
    },
  },
};

// ============================================
// Web Component
// ============================================

export const AsWebComponent: Story = {
  name: 'As Web Component',
  args: {
    name: 'document.pdf',
    downloadUrl: '/download/123',
    size: kbToBytes(2000),
    extension: 'pdf',
  },
  decorators: [withLoader(FILE_ITEM_DEFINITION.tagName)],
  render: ({ name, downloadUrl, size, extension }: any) => (
    <file-nlds
      name={name}
      download-url={downloadUrl}
      size={size}
      extension={extension}
    />
  ),
};
