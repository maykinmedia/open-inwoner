import { AnyComponent } from 'preact';
import { useState } from 'preact/hooks';
import clsx from 'clsx';
import { Button } from '../Button';
import { Input } from '../Input';
import { MaterialIcon } from '../MaterialIcon';
import './Search.scss';
import { useIsMobile } from '@react/lib/hooks';

export type SearchProps = {
  label?: string;
  placeholder?: string;
  initialValue?: string;
  className?: string;
  name?: string;
};

const Search: AnyComponent<SearchProps> = ({
  label = 'Zoeken',
  placeholder = 'Zoeken',
  initialValue = '',
  className,
  name = 'search',
}) => {
  const [value, setValue] = useState(initialValue);
  const isMobile = useIsMobile();

  return (
    <div className={clsx('oip-search', className)}>
      <div className="oip-search__input-wrapper">
        <Input
          label={label}
          name={name}
          type="text"
          value={value}
          placeholder={placeholder}
          onInput={(e) => setValue((e.target as HTMLInputElement).value)}
          noLabel={!isMobile}
        />
        <button
          type="submit"
          class={clsx(
            'oip-search__clear',
            !Boolean(value) && 'oip-search__clear--hidden'
          )}
          onClick={() => setValue('')}
          aria-label="Zoekopdracht wissen"
        >
          <MaterialIcon name="close" />
        </button>
      </div>
      <Button
        variant="primary"
        title="Zoeken"
        type="submit"
        className="oip-search__sumbit"
      >
        <MaterialIcon name="search" />
      </Button>
    </div>
  );
};

export default Search;
