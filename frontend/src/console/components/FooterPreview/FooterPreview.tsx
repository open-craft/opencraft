import * as React from 'react';
import './styles.scss';
import { Col, Row } from 'react-bootstrap';
import { ThemeSchema } from 'ocim-client';
import edxLogo from 'assets/openedx-logo-footer.png';
import messages from './displayMessages';
import { InstanceSettingsModel } from '../../models';
import { WrappedMessage } from '../../../utils/intl';
import { CustomizableLink } from '../CustomizableLink';

interface FooterPreviewProps {
  instanceData: InstanceSettingsModel | null;
  themeData: ThemeSchema;
  loggedIn?: boolean;
}

export const FooterPreview: React.FC<FooterPreviewProps> = (
  props: FooterPreviewProps
) => {
  const { themeData } = props;

  return (
    <div className="custom-footer" style={{ background: themeData.footerBg }}>
      <Row>
        <Col md={5}>
          <Row>
            <Col>
              <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
                About
              </CustomizableLink>
            </Col>
            <Col>
              <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
                Blog
              </CustomizableLink>
            </Col>
            <Col>
              <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
                Contact
              </CustomizableLink>
            </Col>
            <Col>
              <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
                Donate
              </CustomizableLink>
            </Col>
          </Row>
        </Col>
        <Col md={4} />
        <Col md={3} className="openedx-logo">
          <img src={edxLogo} alt="Open edX logo" />
        </Col>
      </Row>
      <Row>
        <Col md={1}>
          {props.instanceData && props.instanceData.logo && (
            <img className="logo" src={props.instanceData.logo} alt="Logo" />
          )}
        </Col>
      </Row>
      <Row>
        <Col className="copyright" style={{ color: themeData.footerColor }}>
          {`© ${props.instanceData && props.instanceData.instanceName}. `}
          <WrappedMessage id="copyright" messages={messages} />
        </Col>
      </Row>
      <Row className="legal">
        <Col>
          <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
            Privacy Policy
          </CustomizableLink>
        </Col>
        <Col>
          <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
            Terms of Service
          </CustomizableLink>
        </Col>
        <Col>
          <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
            Honor Code
          </CustomizableLink>
        </Col>
        <Col>
          <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
            Take free online courses at edX.org
          </CustomizableLink>
        </Col>
        <Col />
      </Row>
    </div>
  );
};
