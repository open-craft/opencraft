import { ROUTES } from "global/constants";
import { RootState } from "global/state";
import * as React from 'react';
import { Button, Form, FormControl, FormGroup, FormLabel, InputGroup } from "react-bootstrap";
import { connect } from "react-redux";
import { WrappedMessage } from "utils/intl";
import { submitRegistration } from "../../actions";
import messages from "./displayMessages";

interface ActionProps {
    submitRegistration: Function
}


interface Props extends ActionProps {

}

interface State {
    domainName: string;
}

@connect<{}, ActionProps, {}, Props, RootState>(
    (state: RootState) => ({}), {
        submitRegistration: submitRegistration,
    }
)
export class DomainInputPage extends React.PureComponent<Props, State> {

    public state: State = {
        domainName: ''
    };

    public render() {
        return (
            <Form>
                <FormGroup>
                    <FormLabel htmlFor="domainNameInput">
                        <WrappedMessage messages={messages} id="typeDomainNameBelow"/>
                    </FormLabel>
                    <InputGroup>
                        <FormControl id="domainNameInput"
                                     defaultValue=""
                                     placeholder="yourdomain"
                                     onChange={this.domainNameChange}/>
                        <InputGroup.Append>
                            <Button onClick={this.submitForm}>
                                <WrappedMessage messages={messages} id="checkAvailability"/>
                            </Button>
                        </InputGroup.Append>
                    </InputGroup>
                </FormGroup>

                <a href="#">
                    <WrappedMessage messages={messages} id="useOwnDomain"/>
                </a>
            </Form>
        )
    }

    private domainNameChange = (event: React.ChangeEvent<HTMLInputElement>) =>
        this.setState({domainName: event.target.value || ''});

    private submitForm = () => {
        this.props.submitRegistration(
            {domain: this.state.domainName},
            ROUTES.Registration.INSTANCE,
        );
    };

}
