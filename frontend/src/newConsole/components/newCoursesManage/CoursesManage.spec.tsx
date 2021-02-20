import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CoursesManage } from './CoursesManage';

/**
 * Finds a tree's child component after following a sequence
 * @param {Object}  component - The root component.
 * @param {Array<Object>} sequence - The sequence of nodes to traverse
 * @return {Object} The targeted component
 */
function getChild(component: Object, sequence: Array<Object>): Object {
  if (sequence.length == 0){
    return component
  } else {
    const target = component.children[sequence.shift()]
    return getChild(target, sequence)
  }

}

it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CoursesManage />).toJSON();
    expect(tree).toMatchSnapshot();
});

it('Correctly renders button with Studio link', () => {
    const tree = setupComponentForTesting(
      <CoursesManage contentLoading={false} showSideBarEditComponent={false}>
      </CoursesManage>,
      {
        console: {
          loading: false,
          activeInstance: {
            data: {
              isEmailVerified: true,
              studioUrl: "test-url",
            },
          }
        }
      }
    ).toJSON();

    const manageCoursesBtn = getChild(tree, [1,0,0,0,1,0,0,3,0]);

    expect(manageCoursesBtn.props.href).toEqual('test-url');
});
