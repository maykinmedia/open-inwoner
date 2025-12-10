import { AnyComponent as AC } from 'preact';
import { MaterialIcon } from '../MaterialIcon';

export interface ILoadingSpinnerProps {
  loadingText?: string;
  iconName?: string;
}

const LoadingSpinner: AC<ILoadingSpinnerProps> = ({
  loadingText = 'Laden...',
  iconName = 'rotate_right',
}) => {
  return (
    <div class="loader-container">
      <div class="spinner">
        <MaterialIcon
          name={iconName}
          extraClassName={['spinner-icon', 'rotate']}
        />
        <div class="spinner__content" role="status">
          {loadingText}
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;
