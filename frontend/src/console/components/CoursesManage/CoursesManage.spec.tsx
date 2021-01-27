import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { CoursesManage } from './CoursesManage';


it('renders without crashing', () => {
    const tree = setupComponentForTesting(<CoursesManage />).toJSON();
    expect(tree).toMatchSnapshot();
});

it('Correctly renders button with Studio link', () => {
    const tree = setupComponentForTesting(
      <CoursesManage contentLoading={false}>
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

    const manageCoursesBtn = tree.children[2].children[0]
    .children[0].children[0].children[1].children[0]
    .children[0].children[0].children[3].children[1].children[0];

    expect(manageCoursesBtn.props.href).toEqual('test-url');
});