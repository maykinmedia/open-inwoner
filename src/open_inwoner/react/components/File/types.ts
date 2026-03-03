export interface IFileProps {
  // Den Haag
  name: string;
  size?: string;
  lastUpdated?: string;
  loading?: boolean;
  className?: string;
  removableLabel?: string;

  // OIP specific
  downloadUrl?: string; /** URL for the download link (Den Haag uses `href`) */
  extension?: string; /** file extension, used to determine icon and display */
  isImage?: boolean; /** force image icon regardless of extension */
  deleteUrl?: string; /** URL for delete redirect, used with showDelete */
  showDelete?: boolean; /** when true, shows delete button instead of download link */
}
