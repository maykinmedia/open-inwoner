import React from 'react';
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import './File.scss';

export function File() {
  return (
    <div className="file">
      <InsertDriveFileOutlinedIcon className="file__icon" />
      <div className="file__name">File name (png, 2MB)</div>
      <div className="file__download">
        <FileDownloadOutlinedIcon className="file__download-icon" />
        Download
      </div>
    </div>
  );
}
