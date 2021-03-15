import * as React from 'react';
// import messages from './displayMessages';
import './styles.scss';
// import { Col, Row } from 'react-bootstrap';
import { ThemeSchema } from 'ocim-client';
// import { CustomizableLink } from '../CustomizableLink';
import { InstanceSettingsModel } from '../../models';

interface CourseContentProps {
  children?: React.ReactNode;
  instanceData: InstanceSettingsModel | null;
  themeData: ThemeSchema;
  loggedIn?: boolean;
}

export const CourseContent: React.FC<CourseContentProps> = (
  props: CourseContentProps
) => {
  // const { themeData } = props;

  const breadcrumbs = () => {

    const linkText = [
      'Course',
      'Example Week 1: Getting Started',
      'Lesson 1 - Getting Started'
    ]
    const renderedLinks : Array<React.ReactNode> = []
    linkText.forEach(link =>
      renderedLinks.push(
        <div>
          <a href='#'>{link}</a>
          &nbsp;
          <i className="fa fa-angle-right"/>
          &nbsp;
        </div>
      )
    )

    return (
      <div>
        {renderedLinks}
        <p>Getting Started</p>
      </div>
    )
  }

  return (
      <div className="breadcrumbs">
        {breadcrumbs()}
        hola
      </div>
  );
};
