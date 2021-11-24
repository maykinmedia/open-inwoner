import React, { MouseEventHandler, ReactElement } from 'react';

import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

import './Pagination.scss';


interface iPaginationProps {
  prevAction: MouseEventHandler,
  nextAction: MouseEventHandler,
  defaultAction: MouseEventHandler,
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
              if (props.currentPage - 3 != 2) {
                return (
                  <>
                    <div key={number} data-page={number} className={getClassNames(number)} onClick={props.defaultAction}>{number}</div>
                    <div key={`${number}-dots`} className="pagination__item">...</div>
                  </>
                )
              }
              return <div key={number} data-page={number} className={getClassNames(number)} onClick={props.defaultAction}>{number}</div>
            }

            if (number == pages()) {
              if (props.currentPage + 4 != pages()) {
                return (
                  <>
                    <div key={`${number}-dots`} className="pagination__item">...</div>
                    <div key={number} data-page={number} className={getClassNames(number)} onClick={props.defaultAction}>{number}</div>
                  </>
                )
              }
              return <div key={number} data-page={number} className={getClassNames(number)} onClick={props.defaultAction}>{number}</div>
            }
          }
        }
      })}
      <div className="pagination__item pagination__item--clickable" onClick={props.nextAction}><ChevronRightIcon /></div>
    </div>
  )
}
