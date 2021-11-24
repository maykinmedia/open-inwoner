import React, { ReactElement, useState, SyntheticEvent } from 'react';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { H4 } from '../Typography/H4';
import { Checkbox } from '../Form/Checkbox';

import './Filter.scss';
import { FaceTwoTone } from '@mui/icons-material';

interface iFilterItem {
  slug: string,
  name: string,
  count: number,
  selected: boolean,
}

interface FilterProps {
  facet: any,
  items: Array<iFilterItem>,
  action: Function,
}

export function Filter(props: FilterProps): ReactElement {
  const { facet, items, action } = props
  const [opened, setOpened] = useState<boolean>(false);

  const renderFilterItems = () => items.map((item: iFilterItem, index: number): ReactElement => {
    return <Checkbox key={ index } onChange={action} field={{ id: item.slug, label: `${item.name} (${item.count})`, name: facet.name, selected: item.selected, value: item.slug, type: "checkbox" }} />;
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
        {facet.name}
        {getIcon()}
      </H4>
      <div className="filter__list">
        {renderFilterItems()}
      </div>
    </aside>
  );
}
