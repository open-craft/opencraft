import * as React from 'react';
import { InstancesModel } from 'console/models';
import { ConsolePage, PreviewBox } from 'newConsole/components';
import { WrappedMessage } from 'utils/intl';
import { Col, Container, Row } from 'react-bootstrap';
import { RootState } from 'global/state';
import { connect } from 'react-redux';
import './styles.scss';
import { INTERNAL_DOMAIN_NAME } from 'global/constants';
import { updateFieldValue } from 'console/actions';
import { DomainListItem } from '../DomainItem';
import messages from './displayMessages';
import { AddDomainButton } from '../AddDomainModalButton';

interface State {
  title: string;
  subtitle: string;
  // extra state to manage the empty title and subtitle and rendering
  renderBool: boolean;
}

interface ActionProps {
  updateFieldValue: Function;
}

interface StateProps extends InstancesModel {}

interface Props extends StateProps, ActionProps {}

export class DomainSettingsComponent extends React.PureComponent<Props, State> {
  private deleteExternalDomain = () => {
    const instance = this.props.activeInstance;
    if (instance.data) {
      this.props.updateFieldValue(instance.data.id, 'externalDomain', null);
    }
  };

  public render() {
    let subdomain;
    let externalDomain;
    let dnsConfigState;
    let externalDomainComponent;
    const instance = this.props.activeInstance;
    if (instance && instance.data) {
      subdomain = instance.data.subdomain;
      externalDomain = instance.data.externalDomain;
      dnsConfigState = instance.data.dnsConfigurationState;
    }

    if (externalDomain) {
      externalDomainComponent = (
        <>
          <hr />
          <DomainListItem
            domainName={externalDomain}
            isExternal
            dnsState={dnsConfigState}
            onDelete={this.deleteExternalDomain}
          />
        </>
      );
    } else {
      externalDomainComponent = <AddDomainButton />;
    }

    return (
      <ConsolePage contentLoading={false} showSideBarEditComponent={false}>
        <PreviewBox>
          <Container className="domain-settings-container">
            <h2>
              <WrappedMessage messages={messages} id="title" />
            </h2>
            <Row>
              <Col className="domain-settings-description">
                <p>
                  <WrappedMessage messages={messages} id="description" />
                </p>
              </Col>
            </Row>
            <div>
              <DomainListItem
                domainName={subdomain + INTERNAL_DOMAIN_NAME}
                isExternal={false}
              />
              {externalDomainComponent}
            </div>
          </Container>
        </PreviewBox>
      </ConsolePage>
    );
  }
}

export const DomainSettings = connect<
  StateProps,
  ActionProps,
  {},
  Props,
  RootState
>((state: RootState) => state.console, {
  updateFieldValue
})(DomainSettingsComponent);
