import React from 'react';
import renderer from 'react-test-renderer';
import { Button } from './Button';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { Router } from 'react-router-dom';

test('Render button', () => {
  const component = renderer.create(
    <Button>Maykin</Button>,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});

// TODO: Render this button
// test('Render link button', () => {
//   const component = renderer.create(
//     <Router>
//       <Button href="/maykin">Maykin</Button>,
//     </Router>
//   );
//   let tree = component.toJSON();
//   expect(tree).toMatchSnapshot();
// });

test('Render anchor button', () => {
  const component = renderer.create(
    <Button href="http://www.maykin.nl">Maykin</Button>,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});

test('Render button with icon', () => {
  const component = renderer.create(
    <Button icon={ArrowForwardIcon}>Maykin</Button>,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});

test('Render button with size', () => {
  const component = renderer.create(
    <Button size="big">Maykin</Button>,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});

test('Render button with open', () => {
  const component = renderer.create(
    <Button open={ true }>Maykin</Button>,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});

test('Render button with primary', () => {
  const component = renderer.create(
    <Button primary={ true }>Maykin</Button>,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});

test('Render button with secondary', () => {
  const component = renderer.create(
    <Button secondary={ true }>Maykin</Button>,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});

test('Render button with transparent', () => {
  const component = renderer.create(
    <Button transparent={ true }>Maykin</Button>,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});

test('Render button without iconPosition', () => {
  const component = renderer.create(
    <Button iconPosition={ undefined }>Maykin</Button>,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});

test('Render button with iconPosition', () => {
  const component = renderer.create(
    <Button iconPosition="after">Maykin</Button>,
  );
  let tree = component.toJSON();
  expect(tree).toMatchSnapshot();
});
