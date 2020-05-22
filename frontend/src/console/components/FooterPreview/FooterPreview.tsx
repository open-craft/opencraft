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
        <Col md={4}>
          <Row className="footer-top-links">
            <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
              <span>About</span>
            </CustomizableLink>
            <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
              <span>Blog</span>
            </CustomizableLink>
            <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
              <span>Contact</span>
            </CustomizableLink>
            <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
              <span>Donate</span>
            </CustomizableLink>
          </Row>
        </Col>
        <Col md={5} />
        <Col md={3} className="openedx-logo">
          <img src={edxLogo} alt="Open edX logo" />
        </Col>
      </Row>
      <Row>
        <Col className="logo" md={1}>
          {props.instanceData && props.instanceData.logo && (
            <img src={props.instanceData.logo} alt="Logo" />
          )}
        </Col>
      </Row>
      <Row>
        <div className="copyright" style={{ color: themeData.footerColor }}>
          {`© ${props.instanceData && props.instanceData.instanceName}. `}
          <WrappedMessage id="copyright" messages={messages} />
        </div>
      </Row>
      <Row className="legal">
        <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
          <span>Privacy Policy</span>
        </CustomizableLink>
        <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
          <span>Terms of Service</span>
        </CustomizableLink>
        <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
          <span>Honor Code</span>
        </CustomizableLink>
        <CustomizableLink linkColor={themeData.footerLinkColor} noHover>
          <span>Take free online courses at edX.org</span>
        </CustomizableLink>
      </Row>
    </div>
  );
};
