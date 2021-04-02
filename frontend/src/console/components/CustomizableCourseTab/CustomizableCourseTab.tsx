import React from 'react';
import { Nav, Navbar } from 'react-bootstrap';
import { CustomizableLink } from '../CustomizableLink';
import './style.scss';

interface CustomizableCourseTabProps {
  children?: React.ReactNode;
  color?: string;
}

export const CustomizableCourseTab: React.FC<CustomizableCourseTabProps> = ({
  color
}: CustomizableCourseTabProps) => {
  return (
    <Navbar bg="transparent" className="theme-course-tabs">
      <Nav className="mr-auto">
        <CustomizableLink
          borderBottomHoverColor={color}
          linkColor={color}
          borderBottomColor={color}
          active
        >
          <span>Course</span>
        </CustomizableLink>
        <CustomizableLink linkHoverColor={color} borderBottomHoverColor={color}>
          <span>Progress</span>
        </CustomizableLink>
        <CustomizableLink linkHoverColor={color} borderBottomHoverColor={color}>
          <span>Discussion</span>
        </CustomizableLink>
        <CustomizableLink linkHoverColor={color} borderBottomHoverColor={color}>
          <span>Wiki</span>
        </CustomizableLink>
      </Nav>
    </Navbar>
  );
};
