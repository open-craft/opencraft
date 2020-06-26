import * as React from 'react';
import './styles.scss';
import { Table, Row, Col } from 'react-bootstrap';
import { WrappedMessage } from 'utils/intl';
import { CollapseEditArea } from '../CollapseEditArea';
import { ColorInputField } from '../ColorInputField';
import { ContentPage } from '../ContentPage';
import { CustomStatusPill } from '../CustomStatusPill';
import { EmailActivationAlertMessage } from '../EmailActivationAlertMessage';
import { StepBar } from '../StepBar';
import { TextInputField } from '../TextInputField';
import messages from './displayMessages';

export const ComponentsDemo: React.FC = () => {
  const [inputColor, setInputColor] = React.useState('#000');
  const [inputTextValue, setInputTextValue] = React.useState('demo page');

  return (
    <div className="components-demo-page">
      <div className="components-demo-heading">
        <h1>Reusable Demo Components</h1>
      </div>
      <div className="components-demo-container">
        <div className="components-demo-text">
          The List of resuable components used inside the OCIM. Before
          generating a new component, check them.
        </div>
        <Table
          striped
          bordered
          hover
          className="components-demo-table-container"
        >
          <thead>
            <tr>
              <th>Component</th>
              <th>Description</th>
              <th>Example</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Collapse Edit Area</td>
              <td>
                Collapse Edit Area component will help create a editing area
                which can be expanded and collapsed based on the props. The Hero
                component has an use case of it.
              </td>
              <td className="collapse-edit-area">
                <CollapseEditArea>
                  <Row>
                    <Col key="exampleCollapseEditArea">
                      <WrappedMessage id="Demo Text" messages={messages} />
                    </Col>
                  </Row>
                </CollapseEditArea>
              </td>
            </tr>
            <tr>
              <td>Color Input Field</td>
              <td>
                Color Input Field component will help create a color input field
                where you can input your colors. The hero component as well as
                many other component has an use case of it.
              </td>
              <td className="color-input-field">
                <ColorInputField
                  fieldName="DemoExampleColor"
                  initialValue={inputColor}
                  messages={messages}
                  onChange={(fieldName: string, newColor: string) => {
                    setInputColor(newColor);
                  }}
                  hideTooltip
                />
              </td>
            </tr>
            <tr>
              <td>Content Page</td>
              <td>
                Content Page component will takes a title and some components as
                its children and provides you a div container with the component
                wrapped inside it. The login has an use case of it.
              </td>
              <td className="table-cell">
                <ContentPage title="Example Page">
                  <WrappedMessage id="Text" messages={messages} />
                </ContentPage>
              </td>
            </tr>
            <tr>
              <td>Custom Status Pill</td>
              <td>
                As the name suggests, the status pill component been used for
                showing instance changes with some colors and text. The
                Redeployment Toolbar has it which shows the progress of
                instance.
              </td>
              <td className="table-cell">
                <CustomStatusPill
                  loading
                  redeploymentStatus={null}
                  deploymentType={null}
                  cancelRedeployment={undefined}
                />
              </td>
            </tr>
            <tr>
              <td>Email Activation Alert Message</td>
              <td>
                This component wraps the WrappedMessage component for an email
                alert which you can see if you have not verified your registered
                email.
              </td>
              <td className="table-cell">
                <EmailActivationAlertMessage />
              </td>
            </tr>
            <tr>
              <td>Step Bar</td>
              <td>
                Step Bar component shows steps pending, registration pages has
                an use case for it.
              </td>
              <td className="table-cell">
                <StepBar count={3} currentStep={2} />
              </td>
            </tr>
            <tr>
              <td>Text Input Field</td>
              <td>A text input field component for inputing the texts.</td>
              <td className="table-cell">
                <TextInputField
                  fieldName="title"
                  messages={messages}
                  value={inputTextValue}
                  onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                    setInputTextValue(event.target.value);
                  }}
                  reset={() => {
                    setInputTextValue('demo page');
                  }}
                  key="demo"
                />
              </td>
            </tr>
          </tbody>
        </Table>
      </div>
    </div>
  );
};
