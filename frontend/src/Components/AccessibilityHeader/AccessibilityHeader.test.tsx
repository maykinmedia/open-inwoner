import React from 'react';
import renderer from 'react-test-renderer';
import { AccessibilityHeader } from './AccessibilityHeader';

test('Render accessibility header', () => {
  const component = renderer.create(
    <AccessibilityHeader />,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});

test('Click zoom accessibility header', () => {
  const component = renderer.create(
    <AccessibilityHeader />,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();

  console.log(tree.children[0].children[0].children[0]);
  tree.children[0].children[0].children[0].onClick();
  expect(tree).toMatchSnapshot();
});
