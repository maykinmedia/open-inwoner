import { describe, expect, it } from 'vitest';
import { render, screen, waitFor } from '@testing-library/preact';
import { useIntl } from 'react-intl';
import { withIntl, IntlWrapperNL, IntlWrapperEN } from './web-component';

const LocaleDisplay = () => {
  const { locale } = useIntl();
  return <div>{locale}</div>;
};

describe('web-component decorators', () => {
  describe('IntlWrapperNL', () => {
    it('provides nl locale', () => {
      render(
        <IntlWrapperNL>
          <LocaleDisplay />
        </IntlWrapperNL>
      );
      expect(screen.getByText('nl')).toBeInTheDocument();
    });
  });

  describe('IntlWrapperEN', () => {
    it('provides en locale', () => {
      render(
        <IntlWrapperEN>
          <LocaleDisplay />
        </IntlWrapperEN>
      );
      expect(screen.getByText('en')).toBeInTheDocument();
    });
  });

  describe('withIntl', () => {
    it('wraps component with I18nProvider', async () => {
      const TestComponent = () => <div>content</div>;
      const Wrapped = withIntl(TestComponent);
      render(<Wrapped />);
      await waitFor(() =>
        expect(screen.getByText('content')).toBeInTheDocument()
      );
    });

    it('passes props through to the wrapped component', async () => {
      const TestComponent = (props: { title: string }) => (
        <div>{props.title}</div>
      );
      const Wrapped = withIntl(TestComponent);
      render(<Wrapped title="hello" />);
      await waitFor(() =>
        expect(screen.getByText('hello')).toBeInTheDocument()
      );
    });
  });
});
