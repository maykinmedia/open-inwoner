import { useContext } from 'react';
import { Link } from 'react-router-dom';
import { globalContext } from '../../store';
import './File.scss';
import InsertDriveFileOutlinedIcon from '@mui/icons-material/InsertDriveFileOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';

export function File() {
  const { globalState, dispatch } = useContext(globalContext);
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
