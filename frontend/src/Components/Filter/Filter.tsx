import React, { ReactElement, useState, SyntheticEvent } from 'react';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { H4 } from '../Typography/H4';
import { Checkbox } from '../Form/Checkbox';

import './Filter.scss';

interface iFilterItem {
  id: string,
  label: string,
  value: any,
  selected: boolean,
}

interface FilterProps {
  title: string,
  items: Array<iFilterItem>,
}

export function Filter(props: FilterProps): ReactElement {
  const { title, items } = props
  const [opened, setOpened] = useState<boolean>(false);

  const renderFilterItems = () => items.map((item: iFilterItem, index: number): ReactElement => {
    return <Checkbox key={ index } field={{ id: item.id, label: item.label, name: item.value, selected: item.selected, value: item.value, type="checkbox" }} />;
  });

  const getIcon = () => {
    if (opened) {
      return <KeyboardArrowUpIcon />
    }
    return <KeyboardArrowDownIcon />
  }

  const toggleOpen = (event: SyntheticEvent) => {
    event.preventDefault();
    setOpened(!opened)
  }

  return (
    <aside className={ opened ? "filter filter--open" : "filter" }>
      <H4 className="filter__title" onClick={ toggleOpen }>
        {title}
        {getIcon()}
      </H4>
      <div className="filter__list">
        {renderFilterItems()}
      </div>
    </aside>
  );
}
