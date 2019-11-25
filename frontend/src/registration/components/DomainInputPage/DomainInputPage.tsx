import { ROUTES } from 'global/constants';
import { RootState } from 'global/state';
import * as React from 'react';
import {
  Button,
  Form,
  FormControl,
  FormGroup,
  FormLabel,
  InputGroup
} from 'react-bootstrap';
import { connect } from 'react-redux';
import { WrappedMessage } from 'utils/intl';
import { InstitutionalAccountHero } from 'ui/components';
import { submitRegistration } from '../../actions';
import { RegistrationPage } from '../RegistrationPage';
import messages from './displayMessages';

interface ActionProps {
  submitRegistration: Function;
}

interface Props extends ActionProps {}

interface State {
  domainName: string;
}

@connect<{}, ActionProps, {}, Props, RootState>((state: RootState) => ({}), {
  submitRegistration
})
export class DomainInputPage extends React.PureComponent<Props, State> {
  public constructor(props: Props, state: State) {
    super(props);
    this.state = {
      domainName: ''
    };
  }

  private domainNameChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    this.setState({
      domainName: event.target.value || ''
    });
  };

  private submitForm = () => {
    console.log(this.state);
    this.props.submitRegistration(
      { domain: this.state.domainName },
      ROUTES.Registration.INSTANCE
    );
  };

  public render() {
    return (
      <div className="div-fill">
        <RegistrationPage
          title="Pro & Teacher Account"
          subtitle="Create your own Open edX instance now."
          currentStep={1}
        >
          <Form>
            <FormGroup>
              <FormLabel htmlFor="domainNameInput">
                <WrappedMessage messages={messages} id="typeDomainNameBelow" />
              </FormLabel>
              <InputGroup>
                <FormControl
                  id="domainNameInput"
                  defaultValue=""
                  placeholder="yourdomain"
                  onChange={this.domainNameChange}
                />
                <InputGroup.Append>
                  <Button onClick={this.submitForm}>
                    <WrappedMessage
                      messages={messages}
                      id="checkAvailability"
                    />
                  </Button>
                </InputGroup.Append>
              </InputGroup>
            </FormGroup>
            <div className="use-own">
              <a href="/#">
                <WrappedMessage messages={messages} id="useOwnDomain" />
              </a>
            </div>
          </Form>
        </RegistrationPage>
        <InstitutionalAccountHero />
      </div>
    );
  }
}
