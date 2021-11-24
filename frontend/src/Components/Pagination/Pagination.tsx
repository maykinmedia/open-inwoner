import React, { ReactElement } from 'react';

import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

import './Pagination.scss';


interface iPaginationProps {
  prevAction: Function,
  nextAction: Function,
  defaultAction: Function,
  currentPage: number,
  itemsPerPage: number,
  totalItems: number,
}

/**
 * Returns an input based on field.
 * @param {iPaginationProps} props
 * @return {ReactElement}
 */
export function Pagination(props: iPaginationProps): ReactElement {
  return (
    <div className="pagination">
      <div className="pagination__item pagination__item--clickable" onClick={props.prevAction}><ChevronLeftIcon /></div>
        <div className="pagination__item pagination__item--clickable pagination__item--active" onClick={props.defaultAction}>1</div>
        <div className="pagination__item pagination__item--clickable" onClick={props.defaultAction}>2</div>
        <div className="pagination__item pagination__item--clickable" onClick={props.defaultAction}>3</div>
        <div className="pagination__item pagination__item--clickable" onClick={props.defaultAction}>4</div>
        <div className="pagination__item">...</div>
        <div className="pagination__item pagination__item--clickable" onClick={props.defaultAction}>10</div>
        <div className="pagination__item pagination__item--clickable" onClick={props.nextAction}><ChevronRightIcon /></div>
      </div>
  )
}
