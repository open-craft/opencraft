import React from 'react';
import { shallow } from 'enzyme';
import { setupComponentForTesting } from "utils/testing";
import { DomainSuccessJumbotron } from './DomainSuccessJumbotron';

it('renders without crashing', () => {
  const tree = setupComponentForTesting(<DomainSuccessJumbotron />).toJSON();
  expect(tree).toMatchSnapshot();
});

it('renders correct text when using external domain', () => {
  const tree = setupComponentForTesting(
    <DomainSuccessJumbotron domain="www.test.com" domainIsExternal={true} />
  ).toJSON();
  expect(tree.children[1].children[0]).toEqual('Your domain name is connected');
  expect(tree.children[2].children[0].children[0]).toEqual('www.test.com');
});

it('renders correct text when using internal domain', () => {
  const tree = setupComponentForTesting(
    <DomainSuccessJumbotron domain="www.test.com" domainIsExternal={false} />
  ).toJSON();
  expect(tree.children[1].children[0]).toEqual('Your domain name is available');
  expect(tree.children[2].children[0].children[0]).toEqual('www.test.com');
});
