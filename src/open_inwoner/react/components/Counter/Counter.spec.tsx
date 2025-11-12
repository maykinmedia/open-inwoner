import { describe, expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { act, useState } from 'react';
import Counter from './Counter';

describe('Counter component', () => {
  const CounterWithCount = () => {
    const [count, setCount] = useState(0);
    return (
      <>
        <div data-testid="count">{count}</div>
        <Counter count={count} setCount={setCount} />
      </>
    );
  };

  test('render the component onto the screen', () => {
    render(<CounterWithCount />);

    expect(screen.getByTestId('count').textContent).toBe('0');
  });

  test('render the component onto the screen and manupilate the count', () => {
    // Create a new component so we can manupulate the state.

    render(<CounterWithCount />);

    expect(screen.getByTestId('count').textContent).toBe('0');

    // Increment counter with one -> new value = '1'
    act(() => {
      screen.getByText('Count increment').click();
    });
    expect(screen.getByTestId('count').textContent).toBe('1');

    // Increment counter with one -> new value = '2'
    act(() => {
      screen.getByText('Count increment').click();
    });
    expect(screen.getByTestId('count').textContent).toBe('2');

    // Decrement counter with one -> new value = '1'
    act(() => {
      screen.getByText('Count decrement').click();
    });
    expect(screen.getByTestId('count').textContent).toBe('1');
  });
});
