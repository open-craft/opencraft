import * as React from 'react';
import { Row } from 'react-bootstrap';
import './styles.scss';
import { StepBar } from 'ui/components/StepBar';

interface Props {
  title: string;
  subtitleBig?: string;
  subtitle?: string;
  children: React.ReactNode;
  currentStep: number;
}

export const RegistrationPage: React.FC<Props> = (props: Props) => {
  return (
    <div className="registration-page">
      <h1>{props.title}</h1>
      {props.subtitleBig && <h1 className="big">{props.subtitleBig}</h1>}
      {props.subtitle && <h2>{props.subtitle}</h2>}

      <div className="step-bar-container">
        <div className="d-flex justify-content-center">
          <StepBar count={4} currentStep={props.currentStep} />
        </div>
      </div>

      <div className="registration-page-container">
        <Row className="registration-page-content">{props.children}</Row>
      </div>
    </div>
  );
};
