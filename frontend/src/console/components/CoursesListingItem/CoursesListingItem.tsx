import * as React from 'react';
import './styles.scss';
import { Col, Row } from 'react-bootstrap';
import { ThemeSchema } from 'ocim-client';
import courseImage from 'assets/course_image.jpg';
import messages from './displayMessages';
import { WrappedMessage } from '../../../utils/intl';
import { CustomizableLink } from '../CustomizableLink';

interface CoursesListingItemProps {
  themeData: ThemeSchema;
  loggedIn?: boolean;
}

export const CoursesListingItem: React.FC<CoursesListingItemProps> = (
  props: CoursesListingItemProps
) => {
  const { themeData } = props;
  const textStyle = { color: themeData.mainColor };
  // TODO: Make text customizable.

  return (
    <Row
      className="courses-listing-item"
      style={{ borderBottomColor: themeData.linkColor }}
    >
      <Col className="course-image">
        <img src={courseImage} alt="course" />
      </Col>
      <Col className="organization" style={textStyle}>
        edX
      </Col>
      <Col className="course-number" style={textStyle}>
        DemoX
      </Col>
      <Col className="course-name">
        <CustomizableLink linkColor={themeData.linkColor} noHover>
          <span>Demonstration Course</span>
        </CustomizableLink>
      </Col>
      <Col className="course-start" style={textStyle}>
        <WrappedMessage messages={messages} id="starts" />
        Feb 5, 2013
      </Col>
    </Row>
  );
};
