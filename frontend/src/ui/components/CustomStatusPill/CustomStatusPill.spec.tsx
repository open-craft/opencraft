import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CustomStatusPill } from './CustomStatusPill';
import { RedeploymentToolbar } from 'console/components/RedeploymentToolbar';
import {
  OpenEdXInstanceDeploymentStatusStatusEnum as DeploymentStatus,
  OpenEdXInstanceDeploymentStatusDeploymentTypeEnum as DeploymentType
} from 'ocim-client';

/**
 * Returns the CustomStatusPill's pillColor and text.
 *
 * This should also return the tooltip text, but we're yet to implement
 * enzyme tests, which are better for testing this type of
 * behavior.
 *
 * @param {Object}  component - The root component.
 * @return {Array<String>} The specified props as an array of strings
 */
function getTestProps(tree: Object): Array<String> {
  const statusPill = tree.children[0].children[0]
  const text = statusPill.children[0].children[0]
  const pillColor = statusPill.props.style.backgroundColor
  return [text, pillColor]
}

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CustomStatusPill />).toJSON();
    expect(tree).toMatchSnapshot();
});

describe('CustomStatusPill renders correctly when ', () => {
    it('Status is Healthy', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={{
            status: DeploymentStatus.Healthy,
            undeployedChanges: [],
            deployedChanges: null,
            type: DeploymentType.Admin,
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(getTestProps(tree)).toEqual(["Up to date","#00a556"]);
    });

    it('Status is Provisioning', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={{
            status: DeploymentStatus.Provisioning,
            undeployedChanges: [],
            deployedChanges: null,
            type: DeploymentType.Admin,
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(getTestProps(tree)).toEqual(["Publishing",'#ff9b04']);
    });

    it('Status is Preparing', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={{
            status: DeploymentStatus.Preparing,
            undeployedChanges: [],
            deployedChanges: null,
            type: DeploymentType.Admin,
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(getTestProps(tree)).toEqual(["Publishing",'#ff9b04']);
    });

    it('Status is ChangesPending', () => {
      const tree = setupComponentForTesting(
        <RedeploymentToolbar
          deployment={{
            status: DeploymentStatus.ChangesPending,
            undeployedChanges: [],
            deployedChanges: null,
            type: DeploymentType.Admin,
          }}
          cancelRedeployment={() => {}}
          performDeployment={() => {}}
        />
      ).toJSON();
      expect(getTestProps(tree)).toEqual(["Publishing",'#00a556']);
    });
});
