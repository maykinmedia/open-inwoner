import React, {ReactElement} from 'react';
import './Grid.scss';

interface GridProps {
  isLoggedIn: boolean,
  children?: any,
  mainContent?: ReactElement,
  sidebarContent?: ReactElement,
}

export function Grid(props: GridProps) {
  const {children, mainContent, sidebarContent, ..._props} = props;

  /**
   * Gets the sidebar content.
   * @return
   */
  const getSidebarContent = (): ReactElement => (
    <>
      {sidebarContent && <aside className="grid__sidebar">
        {sidebarContent}
      </aside>}
    </>
  );

  /**
   * Gets the main content.
   */
  const getMainContent = (): ReactElement => (
    <>
      {(children || mainContent) && <div className="grid__main">
        {mainContent}
        {children}
      </div>}
    </>
  );

  return (
    <div className="grid" {..._props}>
      {getSidebarContent()}
      {getMainContent()}
    </div>
  );
}
