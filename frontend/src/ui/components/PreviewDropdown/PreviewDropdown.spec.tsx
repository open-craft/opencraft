import React from 'react';
import {
    mountComponentForTesting,
    setupComponentForTesting
} from "utils/testing";
import { PreviewDropdown } from './PreviewDropdown';
import messages from './displayMessages'

describe("Preview dropdown", function() {
    it('renders without crashing', () => {
        const tree = setupComponentForTesting(<PreviewDropdown />).toJSON();
        expect(tree).toMatchSnapshot();
    });

    it('renders messages as options', () => {
        messages['somepage'] = {defaultMessage: 'A new page', description: ''};
        const tree = mountComponentForTesting(<PreviewDropdown />);
        const mountedComponent = tree.find('.dropdown-items').find('FormattedMessage');
        expect(mountedComponent.length).toBe(3)
        expect(mountedComponent.children().debug()).toBe('Dashboard\n\n\nCourse Outline\n\n\nA new page')
        expect(tree).toMatchSnapshot();
    });
});
