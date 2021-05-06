import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { ThemeFooterSideBar } from './ThemeFooterSideBar';

describe('Theme footer sidebar tests', () => {
    it('renders without crashing', () => {
        const tree = setupComponentForTesting(
            <ThemeFooterSideBar />,
            {
                console: {
                    history: {
                        goBack: () => {
                            // empty function
                        }
                    },
                    activeInstance: {
                        loading: [],
                        data: {
                            draftThemeConfig: {
                                version: 1,
                                homePageHeroTitleColor: '#000',
                                homePageHeroSubtitleColor: '#999'
                            }
                        }
                    }
                }
            }
            ).toJSON();
        expect(tree).toMatchSnapshot();
    });
})
