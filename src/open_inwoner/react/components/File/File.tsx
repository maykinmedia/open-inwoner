import clsx from 'clsx';
import { AnyComponent as AC } from 'preact';
import { useMemo } from 'preact/hooks';
import { useIntl } from 'react-intl';
import { MaterialIcon } from '../MaterialIcon';
import '@gemeente-denhaag/file/index.css';
import './File.scss';
import { ImageType, FileIcon } from './choices';
import { formatFileSize } from './utils';

export interface IFileProps {
  // Den Haag
  /** The filename, also used to parse the extension when `extension` is not provided */
  name: string;
  /** File size in bytes (as string or number), formatted automatically to KB/MB by formatFileSize */
  size?: string | number;
  /** Optional metadata line displayed below the filename, e.g., "Last updated: ..." */
  lastUpdated?: string;
  /** When true, shows a loading spinner icon instead of the file type icon */
  loading?: boolean;
  /** Additional CSS class applied to the root element */
  className?: string;
  /** Custom label for the delete button, falls back to default translated label */
  removableLabel?: string;

  // OIP specific
  /** URL for the download link */
  downloadUrl?: string;
  /** File extension used to determine the icon and display label; parsed from `name` if not provided */
  extension?: string;
  /** When true, forces the image icon regardless of the extension */
  isImage?: boolean;
  /** URL to call when deleting the file; only used if `showDelete` is true */
  deleteUrl?: string;
  /** When true, shows a delete button instead of the download link */
  showDelete?: boolean;
}

const File: AC<IFileProps> = ({
  name,
  downloadUrl,
  size,
  extension,
  isImage,
  removableLabel,
  deleteUrl,
  lastUpdated,
  loading,
  className,
  showDelete,
}) => {
  const intl = useIntl();

  const displayExtension = useMemo((): string => {
    if (extension) return extension;
    return name?.split('.').pop()?.toLowerCase() || '';
  }, [name, extension]);

  const iconName = useMemo((): string => {
    if (isImage === true) return FileIcon.IMAGE;
    if (Object.values(ImageType).includes(displayExtension as ImageType))
      return FileIcon.IMAGE;
    return FileIcon.DEFAULT;
  }, [isImage, displayExtension]);

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

  const handleDelete = (e: MouseEvent) => {
    e.preventDefault();
    if (deleteUrl && confirm(confirmDeleteText)) {
      window.location.assign(deleteUrl);
    }
  };

  return (
    <div class={clsx('denhaag-file', className)}>
      <div class="denhaag-file__left">
        <MaterialIcon name={loading ? 'rotate_right' : iconName} />
      </div>

      <div class="denhaag-file__right">
        <div class="denhaag-file__label">
          <span>{name}</span>
          {(displayExtension || size) && (
            <span class="denhaag-file--oip__extension">
              {' '}
              ({displayExtension}
              {displayExtension && size && ', '}
              {size && formatFileSize(size)})
            </span>
          )}
          {/* Den Haag meta data */}
          {lastUpdated && <span> — {lastUpdated}</span>}
        </div>

        {showDelete && deleteUrl ? (
          <button
            class="denhaag-file__link denhaag-link--remove"
            onClick={handleDelete}
            type="button"
          >
            <MaterialIcon name="delete" />
            {(removableLabel || deleteLabelDefault) && (
              <span>{removableLabel || deleteLabelDefault}</span>
            )}
          </button>
        ) : downloadUrl ? (
          <a href={downloadUrl} download={name} class="denhaag-file__link">
            <MaterialIcon name="download" />
            <span>{downloadLabel}</span>
          </a>
        ) : null}
      </div>
    </div>
  );
};

export default File;
