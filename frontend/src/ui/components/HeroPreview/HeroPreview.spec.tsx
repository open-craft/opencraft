import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { HeroPreview } from './HeroPreview';

describe("Hero preview component", function() {
    it('renders without crashing', () => {
        const tree = setupComponentForTesting(<HeroPreview />).toJSON();
        expect(tree).toMatchSnapshot();
    });
    it('renders without crashing when instance has no theme set up', () => {
          const tree = setupComponentForTesting(
          <HeroPreview
            homepageOverlayHtml="<h1>Welcome to Test instance</h1><p>It works! Powered by Open edX®</p>"
            heroCoverImage="https://example.com/image.png"
          />
        ).toJSON();
        expect(tree).toMatchSnapshot();
    });
    it('renders without crashing when instance has no home page overlay html provided', () => {
      const tree = setupComponentForTesting(
          <HeroPreview
            heroCoverImage="https://example.com/image.png"
            homePageHeroTitleColor='#000'
            homePageHeroSubtitleColor='#999'
          />
        ).toJSON();
        expect(tree).toMatchSnapshot();
    });
    it('renders without crashing when instance has no cover image provided', () => {
      const tree = setupComponentForTesting(
          <HeroPreview
            homePageHeroTitleColor='#000'
            homePageHeroSubtitleColor='#999'
            homepageOverlayHtml="<h1>Welcome to Test instance</h1><p>It works! Powered by Open edX®</p>"
          />
        ).toJSON();
        expect(tree).toMatchSnapshot();
    });
    it('renders without crashing when the instance only has the cover image provided', () => {
      const tree = setupComponentForTesting(
          <HeroPreview
            heroCoverImage="https://example.com/image.png"
          />
        ).toJSON();
        expect(tree).toMatchSnapshot();
    });
    it('renders without crashing when the instance only has the home page overlay html provided', () => {
      const tree = setupComponentForTesting(
          <HeroPreview
            homepageOverlayHtml="<h1>Welcome to Test instance</h1><p>It works! Powered by Open edX®</p>"
          />
        ).toJSON();
        expect(tree).toMatchSnapshot();
    });
    it('renders without crashing when the instance only has the theme config set up', () => {
      const tree = setupComponentForTesting(
          <HeroPreview
            homePageHeroTitleColor='#000'
            homePageHeroSubtitleColor='#999'
          />
        ).toJSON();
        expect(tree).toMatchSnapshot();
    });
    it('renders without crashing when the instance only has the hero title color set up', () => {
      const tree = setupComponentForTesting(
          <HeroPreview
            homePageHeroTitleColor='#000'
          />
        ).toJSON();
        expect(tree).toMatchSnapshot();
    });
    it('renders without crashing when the instance only has the hero subtitle color set up', () => {
      const tree = setupComponentForTesting(
          <HeroPreview
            homePageHeroSubtitleColor='#000'
          />
        ).toJSON();
        expect(tree).toMatchSnapshot();
    });
});
