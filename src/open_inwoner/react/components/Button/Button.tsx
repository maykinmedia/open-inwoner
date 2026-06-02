import clsx from 'clsx';
import {
  AnyComponent as AC,
  ButtonHTMLAttributes,
  MouseEventHandler,
} from 'preact';
import './Button.scss';

export type ButtonProps = {
  text?: string;
  handleClick?: MouseEventHandler<HTMLButtonElement>;
  variant: 'primary' | 'secondary';
  transparent?: boolean;
  className?: string;
  iconSize?: 'md' | 'lg';
  underline?: 'none' | 'hover';
  fullWidth?: boolean;
} & ButtonHTMLAttributes;

const Button: AC<ButtonProps> = ({
  text,
  handleClick,
  title,
  variant = 'primary',
  children,
  transparent,
  type = 'button',
  className,
  iconSize,
  underline = 'none',
  disabled,
  fullWidth = false,
  ...props
}) => {
  return (
    <button
      {...props}
      type={type}
      className={clsx(
        'button',
        `button--${variant}`,
        {
          ['button--transparent']: transparent,
          ['button--fullwidth']: fullWidth,
          ['button--disabled']: disabled,
          ['button--textless']: !text,
          ['button--icon']: !text,
          ['button--icon-lg']: iconSize == 'lg',
          ['button--no-underline']: underline === 'none',
        },
        className
      )}
      onClick={handleClick}
      title={title || text}
      aria-label={text || title}
      disabled={disabled}
    >
      {text ? <span class="button__inner-text">{text}</span> : children}
    </button>
  );
};

export default Button;
