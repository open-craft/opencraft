import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { createMemoryHistory } from 'history';
import { CustomizationSideMenu } from './CustomizationSideMenu';
import routeData from 'react-router';

describe("Custom Side Menu Page", function() {
  const mockLocation = {
    pathname: '/console/settings/general',
    hash: '',
    search: '',
    state: ''
  }
  beforeEach(() => {
    jest.spyOn(routeData, 'useLocation').mockReturnValue(mockLocation)
  });

  it('Renders with correct accordion expanded, and with current page highlighted', () => {
    const tree = setupComponentForTesting(<CustomizationSideMenu />).toJSON();
    expect(tree).toMatchSnapshot();
  });
});
