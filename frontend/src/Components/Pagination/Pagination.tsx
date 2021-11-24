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
  const pages = () => {
    console.log(props.totalItems / props.itemsPerPage, props.totalItems, props.itemsPerPage)
    return Math.ceil(props.totalItems / props.itemsPerPage);
  }

  const pagesList = () => {
    let list = [...Array(pages() + 1).keys()]
    list.splice(0, 1)
    return list;
  }

  const getClassNames = (number: number) => {
    let classnames = "pagination__item pagination__item--clickable"

    if (number == props.currentPage) {
      classnames += " pagination__item--active"
    }
    return classnames
  }

  if (props.totalItems <= props.itemsPerPage) {
    return <></>;
  }
  return (
    <div className="pagination">
      <div className="pagination__item pagination__item--clickable" onClick={props.prevAction}><ChevronLeftIcon /></div>
      {pagesList().map((number) => {
        if (props.currentPage == number) {
          return <div key={number} data-page={number} className={getClassNames(number)} onClick={props.defaultAction}>{number}</div>
        } else {
          if (number - 3 <= props.currentPage && props.currentPage <= number + 3) {
            return <div key={number} data-page={number} className={getClassNames(number)} onClick={props.defaultAction}>{number}</div>
          } else {
            if (number == 1) {
              return <div key={number} data-page={number} className={getClassNames(number)} onClick={props.defaultAction}>{number}</div>
            }

            if (props.currentPage - 3 != 2) {
              return <div className="pagination__item">...</div>
            }
          }

          if (number == pages()) {
            if (props.currentPage + 4 != pages()) {
              return <div className="pagination__item">...</div>
            }

            return <div key={number} data-page={number} className={getClassNames(number)} onClick={props.defaultAction}>{number}</div>
          }
        }
      })}
      {/* <div data-page={2} className="pagination__item pagination__item--clickable" onClick={props.defaultAction}>2</div>
      <div data-page={3} className="pagination__item pagination__item--clickable" onClick={props.defaultAction}>3</div>
      <div data-page={4} className="pagination__item pagination__item--clickable" onClick={props.defaultAction}>4</div>
      <div className="pagination__item">...</div>
      <div data-page={10} className="pagination__item pagination__item--clickable" onClick={props.defaultAction}>10</div> */}
      <div className="pagination__item pagination__item--clickable" onClick={props.nextAction}><ChevronRightIcon /></div>
    </div>
  )
}
