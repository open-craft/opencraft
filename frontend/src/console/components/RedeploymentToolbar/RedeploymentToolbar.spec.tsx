import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { RedeploymentToolbar } from './RedeploymentToolbar';
import {
    OpenEdXInstanceDeploymentStatusDeploymentTypeEnum,
    OpenEdXInstanceDeploymentStatusStatusEnum
} from 'ocim-client';


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
            status: OpenEdXInstanceDeploymentStatusStatusEnum.Preparing,
            undeployedChanges: [],
            deployedChanges: null,
            type: OpenEdXInstanceDeploymentStatusDeploymentTypeEnum.Admin,
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
            status: OpenEdXInstanceDeploymentStatusStatusEnum.Healthy,
            undeployedChanges: [],
            deployedChanges: null,
            type: OpenEdXInstanceDeploymentStatusDeploymentTypeEnum.Admin,
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
            status: OpenEdXInstanceDeploymentStatusStatusEnum.ChangesPending,
            undeployedChanges: [[], [], []],
            deployedChanges: null,
            type: OpenEdXInstanceDeploymentStatusDeploymentTypeEnum.User,
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Correctly renders redeployment bar when deployment is by admin', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={{
            status: OpenEdXInstanceDeploymentStatusStatusEnum.ChangesPending,
            undeployedChanges: [[], [], []],
            deployedChanges: null,
            type: OpenEdXInstanceDeploymentStatusDeploymentTypeEnum.Admin,
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });

  it('Correctly renders redeployment bar when instance is being deployed by user', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={{
            status: OpenEdXInstanceDeploymentStatusStatusEnum.Provisioning,
            undeployedChanges: [],
            deployedChanges: null,
            type: OpenEdXInstanceDeploymentStatusDeploymentTypeEnum.User,
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(tree).toMatchSnapshot();
  });
});
