import { AnyComponent as AC } from 'preact';
import { MaterialIcon } from '../MaterialIcon';
import './Spinner.scss';
import clsx from 'clsx';

export interface ILoadingSpinnerProps {
  loadingText?: string;
  iconName?: string;
  compact?: boolean;
}

const LoadingSpinner: AC<ILoadingSpinnerProps> = ({
  loadingText = 'Laden...',
  iconName = 'rotate_right',
  compact = false,
}) => {
  return (
    <div
      class={clsx('loader-container', compact && 'loader-container--compact')}
    >
      <div class="spinner">
        <MaterialIcon
          name={iconName}
          extraClassName={['spinner-icon', 'rotate']}
        />
        <div class="spinner__content" aria-hidden="true">
          {loadingText}
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;
