import { ROUTES } from "global/constants";
import * as React from 'react';
import { Col, Jumbotron } from "react-bootstrap";
import { Link } from "react-router-dom";
import './styles.scss';

export const Home: React.FC = () => (
    <Col>
        <Jumbotron>
            <h1>
                This is the home page
            </h1>
            <Link to={ROUTES.Registration.HOME} className="btn btn-primary">
                Start Registration
            </Link>
        </Jumbotron>
    </Col>
);
