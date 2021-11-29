import React, {ReactElement} from 'react';
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined';
import ImageOutlinedIcon from '@mui/icons-material/ImageOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined';
import {SvgIconTypeMap} from '@mui/material';
import {OverridableComponent} from '@mui/material/OverridableComponent';
import {Link} from '../Typography/Link';
import {P} from '../Typography/P';
import './File.scss';


export interface iFileProps {
  extension: string,
  label: string,
  size: number
  url: string,
}

/**
 * A downloadable file.
 * @param {iFileProps} props
 * @return {ReactElement}
 */
export function File(props: iFileProps): ReactElement {
  const {extension, label, size, url, ..._props} = props;

  /**
   * Returns the correct icon component.
   * @return {OverridableComponent}
   */
  const getIconComponent = (): OverridableComponent<SvgIconTypeMap> => {
    const documentTypes = ['doc', 'docx', 'odp', 'ods', 'odt', 'pdf', 'rtf', 'txt', 'xls', 'xlsx', 'ppt', 'pptx']
    const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'svg'];
    const _extension = extension.toLowerCase().trim().replace('.', '');

    if (documentTypes.indexOf(_extension) > -1) {
      return DescriptionOutlinedIcon;
    }

    if (imageTypes.indexOf(_extension) > -1) {
      return ImageOutlinedIcon;
    }

    return InsertDriveFileOutlinedIcon;
  }

  const getFileSizeLabel = () => {
    const kb = size * 0.001;

    if (kb < 1000) {
      return kb.toFixed(2) + 'KB';
    }

    const mb = kb * 0.001;
    return mb.toFixed(2) + 'MB';
  }


  const Icon = getIconComponent();

  return (
    <aside className="file" {..._props}>
      <Icon/>
      <P>{label} ({extension}, {getFileSizeLabel()})</P>
      <Link download={true} icon={FileDownloadOutlinedIcon} secondary={true} shouldRenderExternalIcon={false} to={url}>
        Download
      </Link>
    </aside>
  );
}
