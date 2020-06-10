import * as React from 'react';
// import messages from './displayMessages';
import './styles.scss';
import { Table } from 'react-bootstrap';
// import { WrappedMessage } from 'utils/intl';

export const ComponentsDemo: React.FC = () => (
  <div className="components-demo-page">
    <div className="components-demo-heading">
      <h1>Reusable Demo Components</h1>
    </div>
    <div className="components-demo-container">
      <div className="components-demo-text">
        The List of resuable components used inside the OCIM. Before generating
        a new component, check them.
      </div>
      <Table striped bordered hover className="components-demo-table-container">
        <thead>
          <tr>
            <th>Component</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Collapse Edit Area</td>
            <td>
              Collapse Edit Area component will help create a editing area which
              can be expanded and collapsed based on the props. The Hero
              component has an use case of it.
            </td>
          </tr>
          <tr>
            <td>Color Input Field</td>
            <td>
              Color Input Field component will help create a color input field
              where you can input your colors. The hero component as well as
              many other component has an use case of it.
            </td>
          </tr>
          <tr>
            <td>Content Page</td>
            <td>
              Content Page component will takes a title and some components as
              it's children and provides you a div container with the component
              wrapped inside it. The login has an use case of it.
            </td>
          </tr>
          <tr>
            <td>Custom Status Pill</td>
            <td>
              As the name suggests, the status pill component been used for
              showing instance changes with some colors and text. The
              Redeployment Toolbar has it which shows the progress of instance.
            </td>
          </tr>
          <tr>
            <td>Domain Success Jumbotron</td>
            <td>
              This component wraps the Jumbotron react bootstrap component which
              extend the entire viewport to showcase key content on your site.
            </td>
          </tr>
          <tr>
            <td>Email Activation Alert Message</td>
            <td>
              This component wraps the WrappedMessage component for an email
              alert which you can see if you haven't verified your registered
              email.
            </td>
          </tr>
          <tr>
            <td>Footer</td>
            <td>
              It's the footer component which shows you copyright and trademark
              messages.
            </td>
          </tr>
          <tr>
            <td>Header</td>
            <td>
              Header bar component for showing the Opencraft logo, create your
              account, login buttons.
            </td>
          </tr>
          <tr>
            <td>Image Upload Field</td>
            <td>
              This component will be used for uploading the images, logos
              component has use case for it.
            </td>
          </tr>
          <tr>
            <td>Step Bar</td>
            <td>
              Step Bar component shows steps pending, registration pages has an
              use case for it.
            </td>
          </tr>
          <tr>
            <td>Text Input Field</td>
            <td>A text input field component for inputing the texts.</td>
          </tr>
        </tbody>
      </Table>
    </div>
  </div>
);
