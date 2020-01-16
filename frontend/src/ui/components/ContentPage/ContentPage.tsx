import * as React from 'react';
import { Row } from 'react-bootstrap';
import './styles.scss';

interface Props {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  headerExtra?: React.ReactNode;
}

export const ContentPage: React.FC<Props> = (props: Props) => {
  return (
    <div className="content-page">
      <div className="title-container">
        <h1>{props.title}</h1>
        {props.subtitle && <h2>{props.subtitle}</h2>}

        {props.headerExtra}
      </div>

      <div className="content-page-container">
        <Row className="content-page-content">{props.children}</Row>
      </div>
    </div>
  );
};
