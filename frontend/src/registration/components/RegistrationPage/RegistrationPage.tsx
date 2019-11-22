import { ReactNode } from 'react';
import * as React from 'react';
import { Row } from 'react-bootstrap';
// import messages from './displayMessages';
import './styles.scss';
import { StepBar } from 'ui/components/StepBar';

interface Props {
    title: string;
    subtitle?: string;
    children: ReactNode;
    currentStep: number;
}

export const RegistrationPage: React.FC<Props> = ({
  title, subtitle, children, currentStep,
}) => (
  <div className="registration-page">
    <h1>{title}</h1>
    {subtitle && <h2>{subtitle}</h2>}
    <div className="d-flex justify-content-center">
      <StepBar count={4} currentStep={currentStep} />
    </div>

    <div className="registration-page-container">
      <Row className="registration-page-content">
        {children}
      </Row>
    </div>
  </div>
);
