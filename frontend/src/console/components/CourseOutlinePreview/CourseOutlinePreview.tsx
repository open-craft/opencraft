import React from 'react';
import {
  Accordion,
  Button,
  Col,
  Container,
  Form,
  FormControl,
  Navbar,
  Row
} from 'react-bootstrap';
import { NavigationMenu } from 'console/components/NavigationMenu';
import { InstanceSettingsModel } from 'console/models';
import {
  FooterPreview,
  CustomizableButton,
  CustomizableLink,
  CustomizableCourseTab
} from 'console/components';

import './style.scss';

interface CourseOutlineItemsProps {
  instanceData: InstanceSettingsModel;
}

interface SubSection {
  title: string;
  icon?: string;
}

interface Section {
  title: string;
  items: Array<SubSection>;
}

const COURSE_OUTLINE_ITEMS: Array<Section> = [
  {
    title: 'Introduction',
    items: [{ title: 'Demo Course Overview' }]
  },
  {
    title: 'Example Week 1: Getting Started',
    items: [
      { title: 'Lesson 1 - Getting Started' },
      { title: 'Homework - Question Styles (7 Questions)', icon: 'far fa-edit' }
    ]
  },
  {
    title: 'Example Week 2: Get Interactive',
    items: [
      { title: "Lesson 2 - Let's Get Interactive!" },
      { title: 'Homework - Lab and Demos (5 Questions)' },
      { title: 'Homework - Essays' }
    ]
  },
  {
    title: 'Example Week 3: Be Social',
    items: [
      { title: 'Lesson 3 - Be Social' },
      { title: 'Homework - Find Your Study Buddy' },
      { title: 'More Ways to Connect' }
    ]
  },
  {
    title: 'About Exams and Certificates',
    items: [{ title: 'edX Exams (6 Questions)' }]
  }
];

const CourseOutlineItems: React.FC<CourseOutlineItemsProps> = (
  props: CourseOutlineItemsProps
) => {
  const { instanceData } = props;
  const themeData = instanceData.draftThemeConfig;

  const arrowStyle = {
    color: themeData?.linkColor
  };

  return (
    <Accordion defaultActiveKey="0" className="theme-course-outline-tree">
      {/* eslint-disable react/no-array-index-key */}
      {COURSE_OUTLINE_ITEMS.map((section, index) => (
        <div key={`section-${index}`} className="course-outline-section">
          <Accordion.Toggle
            as={Button}
            variant="link"
            className="toggle-btn"
            eventKey={`${index}`}
          >
            <span className="fa fa-chevron-right" style={arrowStyle} />
            {section.title}
          </Accordion.Toggle>
          <Accordion.Collapse eventKey={`${index}`}>
            <div className="course-outline-subsection">
              {section.items.map((subsection, idx) => (
                <CustomizableLink
                  key={`subsection-${idx}`}
                  linkColor={themeData?.linkColor}
                >
                  {subsection.icon && <span className={subsection.icon} />}
                  {subsection.title}
                </CustomizableLink>
              ))}
            </div>
          </Accordion.Collapse>
        </div>
      ))}
    </Accordion>
  );
};

interface CourseOutlinePreviewProps {
  children?: React.ReactNode;
  instanceData: InstanceSettingsModel;
}

export const CourseOutlinePreview: React.FC<CourseOutlinePreviewProps> = (
  props: CourseOutlinePreviewProps
) => {
  const { instanceData } = props;
  const themeData = instanceData.draftThemeConfig!;
  return (
    <>
      <Container className="theme-preview-navigation" fluid>
        <NavigationMenu
          instanceData={instanceData}
          themeData={themeData}
          coursePage
          loggedIn
        />
      </Container>
      <div className="theme-outline">
        <CustomizableCourseTab color={themeData.linkColor} />
        <div className="theme-course-outline-view">
          <Navbar className="outline-header">
            <h2 className="m-0">Demonstration Course</h2>
            <Form inline className="ml-auto mr-1">
              <FormControl
                type="text"
                placeholder="Search"
                className="mr-0 searchBox"
              />
              <CustomizableButton
                initialTextColor={themeData.btnSecondaryColor}
                initialBorderColor={themeData.btnSecondaryBorderColor}
                initialBackgroundColor={themeData.btnSecondaryBg}
                initialHoverTextColor={themeData.btnSecondaryHoverColor}
                initialHoverBackgroundColor={themeData.btnSecondaryHoverBg}
                initialHoverBorderColor={themeData.btnSecondaryHoverBorderColor}
              >
                Search
              </CustomizableButton>
            </Form>
            <CustomizableButton
              initialTextColor={themeData.btnPrimaryColor}
              initialBorderColor={themeData.btnPrimaryBorderColor}
              initialBackgroundColor={themeData.btnPrimaryBg}
              initialHoverTextColor={themeData.btnPrimaryHoverColor}
              initialHoverBackgroundColor={themeData.btnPrimaryHoverBg}
              initialHoverBorderColor={themeData.btnPrimaryHoverBorderColor}
            >
              Start Course
            </CustomizableButton>
          </Navbar>
          <div className="outline-body">
            <div className="outline-container">
              <div className="outline-tree-action-wrapper">
                <CustomizableButton
                  initialTextColor={themeData.btnSecondaryColor}
                  initialBorderColor={themeData.btnSecondaryBorderColor}
                  initialBackgroundColor={themeData.btnSecondaryBg}
                  initialHoverTextColor={themeData.btnSecondaryHoverColor}
                  initialHoverBackgroundColor={themeData.btnSecondaryHoverBg}
                  initialHoverBorderColor={
                    themeData.btnSecondaryHoverBorderColor
                  }
                >
                  Expand All
                </CustomizableButton>
              </div>

              <CourseOutlineItems instanceData={instanceData} />
            </div>
            <div className="course-outline-sidebar">
              <div className="sidebar-section">
                <h3 className="hd-6">Course Tools</h3>
                <ul className="list-unstyled">
                  <li>
                    <CustomizableLink linkColor={themeData.linkColor}>
                      <i className="fa fa-bookmark" />
                      Bookmarks
                    </CustomizableLink>
                  </li>
                </ul>
              </div>
              <div className="sidebar-section">
                <h3 className="hd-6">Course Handouts</h3>
                <ol>
                  <li>
                    <CustomizableLink linkColor={themeData.linkColor}>
                      Example handout
                    </CustomizableLink>
                  </li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>
      <Row className="theme-footer">
        <Col>
          <FooterPreview instanceData={instanceData} themeData={themeData} />
        </Col>
      </Row>
    </>
  );
};
