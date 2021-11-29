import React, {ReactElement} from 'react';
import {H4} from '../Typography/H4';
import {iFileProps, File} from './File';
import './FileList.scss';


interface iFileListProps {
  id?: string,
  files: iFileProps[],
  title?: string
}


/**
 * Renders a file list.
 * @param {iFileListProps} props
 * @return {ReactElement|null}
 */
export function FileList(props: iFileListProps):React.ReactElement | null {
  const {id, files, title, ..._props} = props;


  /**
   * Returns the list items.
   * @return {ReactElement[]}
   */
  const getListItems = (): ReactElement[] => files.map((fileProps: iFileProps, index: number): ReactElement => {
    return (
      <li key={index} className="file-list__list-item">
        <File {...fileProps}/>
      </li>
    );
  }) || []

  if(!files?.length) {
    return null;
  }

  return (
    <nav className="file-list" {..._props}>
      <H4 id={id}>{title}</H4>
      <ul className="file-list__list">
        {getListItems()}
      </ul>
    </nav>
  );
}

FileList.defaultProps = {
  title: 'Bestanden'
}
