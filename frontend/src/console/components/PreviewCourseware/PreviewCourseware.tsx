import * as React from 'react';
import './styles.scss';
import { Col, Row } from 'react-bootstrap';
import { InstanceSettingsModel } from '../../models';
import { NavigationMenu } from './NavigationMenu';
import { CourseContent } from './CourseContent';

interface PreviewCoursewareProps {
    instanceData: InstanceSettingsModel;
}


export const PreviewCourseware: React.FC<PreviewCoursewareProps> = (
    props: PreviewCoursewareProps
) => {
    const { instanceData } = props;
    const themeData = instanceData.draftThemeConfig!;

    return (
        <div className="theme-preview">
            <Row className="theme-preview-navigation">
              <Col className="theme-preview-navigation">
                  <NavigationMenu
                    instanceData={instanceData}
                    themeData={themeData}
                  />
              </Col>
            </Row>
            <div className="theme-home">
            <Row className="theme-courses-container">
                <Col className="theme-preview-course">
                    <CourseContent
                        instanceData={instanceData}
                        themeData={themeData}
                    />
                </Col>
            </Row>
            </div>
        </div>
    )

};
