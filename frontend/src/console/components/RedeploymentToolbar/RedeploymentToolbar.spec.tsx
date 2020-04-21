import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { RedeploymentToolbar } from './RedeploymentToolbar';
import { OpenEdXInstanceDeploymentStatusStatusEnum } from 'ocim-client';


describe("RedeploymentToolbar Component", function() {
  it('Correctly renders redeployment bar when deployment info isn\'t there', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={undefined}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Correctly renders redeployment bar when instance is being prepared', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={{
            status: OpenEdXInstanceDeploymentStatusStatusEnum.PREPARINGINSTANCE,
            undeployedChanges: 0
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Correctly renders redeployment bar when instance is up-to-date', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={{
            status: OpenEdXInstanceDeploymentStatusStatusEnum.UPTODATE,
            undeployedChanges: 0
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Correctly renders redeployment bar when instance has pending changes', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={{
            status: OpenEdXInstanceDeploymentStatusStatusEnum.PENDINGCHANGES,
            undeployedChanges: 3
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Correctly renders redeployment bar when instance is being deployed', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={{
            status: OpenEdXInstanceDeploymentStatusStatusEnum.DEPLOYING,
            undeployedChanges: 0
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });
});
