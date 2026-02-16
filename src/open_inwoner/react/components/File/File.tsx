import { AnyComponent as AC } from 'preact';
import { useIntl } from 'react-intl';
import { MaterialIcon } from '../MaterialIcon';
import '@gemeente-denhaag/file/index.css';
import './File-nlds.scss';

export interface IFileProps {
  name: string;
  size?: string;
  href?: string;
  extension?: string;
  isImage?: boolean;
  removable?: boolean;
  removableLabel?: string;
  deleteUrl?: string;
  lastUpdated?: string;
  loading?: boolean;
  className?: string;
  showDownload?: boolean;
  showDelete?: boolean;
}

type FileComponentProps = IFileProps;

const File: AC<FileComponentProps> = ({
  name,
  href,
  size,
  extension,
  isImage,
  removable,
  removableLabel,
  deleteUrl,
  lastUpdated,
  loading,
  className,
  showDownload = true,
  showDelete,
}) => {
  const intl = useIntl();

  const IMAGE_TYPES = [
    'jpg',
    'jpeg',
    'png',
    'gif',
    'webp',
    'tiff',
    'tif',
    'svg',
  ];

  const getIconName = (isImg?: boolean, ext?: string): string => {
    if (isImg === true) return 'image';
    const extLower = ext?.toLowerCase();
    if (IMAGE_TYPES.includes(extLower || '')) return 'image';
    return 'insert_drive_file';
  };

  const confirmDeleteText = intl.formatMessage({
    id: 'file.confirmDelete',
    description: 'Confirmation dialog when deleting a file',
    defaultMessage: 'Are you sure you want to delete this file?',
  });

  const deleteLabelDefault = intl.formatMessage({
    id: 'file.delete',
    description: 'Delete button label',
    defaultMessage: 'Delete',
  });

  const downloadLabel = intl.formatMessage({
    id: 'file.download',
    description: 'Download button label',
    defaultMessage: 'Download',
  });

  const handleDelete = (url: string) => (e: MouseEvent) => {
    e.preventDefault();
    if (confirm(confirmDeleteText)) {
      window.location.href = url;
    }
  };

  return (
    <div class={`denhaag-file ${className || ''}`}>
      <div class="denhaag-file__left">
        {loading ? (
          <span class="loading">⟳</span>
        ) : (
          <MaterialIcon
            name={getIconName(isImage, extension)}
            outlined={true}
          />
        )}
      </div>

      <div class="denhaag-file__right">
        <div class="denhaag-file__label">
          <span>{name}</span>
          {extension && <span> ({extension}</span>}
          {size && <span>, {size})</span>}
          {lastUpdated && <span> — {lastUpdated}</span>}
        </div>

        {(showDelete ?? removable) && deleteUrl ? (
          <button
            class="denhaag-file__link denhaag-link--remove"
            onClick={handleDelete(deleteUrl)}
            type="button"
          >
            <MaterialIcon name="delete" outlined={true} />
            <div>{removableLabel || deleteLabelDefault}</div>
          </button>
        ) : (showDownload ?? true) ? (
          <a href={href} download={name} class="denhaag-file__link">
            <MaterialIcon name="download" outlined={true} />
            <div>{downloadLabel}</div>
          </a>
        ) : null}
      </div>
    </div>
  );
};

export default File as AC<FileComponentProps>;
