import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomPages } from './CustomPages';

describe("Custom Side Menu Page", function() {
  const mockLocationProps = {
    params: {
      pageName: "about"
    }
  }

  it('renders without crashing', () => {
    // This does not generate or use a snapshot!
    // Only checks if the component is properly rendered using state.
    // Not using snapshot here because TinyMCE renders with a
    // different ID everytime.
    setupComponentForTesting(
        <CustomPages match={mockLocationProps}/>,
        {
          console: {
            loading: false,
            activeInstance: {
              data: {
                id: 1,
                instanceName: "test",
                subdomain: "test",
                draftStaticContentOverrides: {
                  staticTemplateAboutContent: "<p>test import from state</p>"
                }
              },
              loading: []
            }
          }
        }
    ).toJSON();
  });
});
