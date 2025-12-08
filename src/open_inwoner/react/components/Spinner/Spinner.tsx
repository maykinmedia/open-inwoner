import { AnyComponent as FC } from 'preact';
// import { usePropsOrScriptData } from '@react/lib/json/getJsonScriptData';

export interface ILoadingSpinnerProps {
  loadingText?: string;
  iconName?: string;
}

const LoadingSpinner: FC<ILoadingSpinnerProps> = ({
  loadingText = 'Laden...',
  iconName = 'rotate_right',
}) => {
  return (
    <div class="loader-container">
      <div class="spinner">
        <span class="material-icons spinner-icon rotate" aria-hidden="true">
          {iconName}
        </span>
        <div class="spinner__content" role="status">
          {loadingText}
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;
