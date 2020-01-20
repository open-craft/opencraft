import * as React from 'react';
import { Row } from 'react-bootstrap';
import './styles.scss';

interface Props {
  title: any;
  subtitle?: any;
  children: React.ReactNode;
  titleExtra?: React.ReactNode;
  toolbar?: React.ReactNode;
}

export const ContentPage: React.FC<Props> = (props: Props) => {
  return (
    <div className="content-page">
      <div className="title-container">
        <h1>{props.title}</h1>
        {props.subtitle && <h2>{props.subtitle}</h2>}

        {props.titleExtra}
      </div>

      {props.toolbar}

      <div className="content-page-container">
        <Row className="content-page-content">{props.children}</Row>
      </div>
    </div>
  );
};
