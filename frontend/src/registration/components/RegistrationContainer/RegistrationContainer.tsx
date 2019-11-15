import * as React from 'react';
import { Col } from "react-bootstrap";
import { RegistrationRoutes } from "routes/registration";
import './styles.scss';

export const RegistrationContainer: React.FC = () => {
    return (
        <Col className="registration-container">
            <RegistrationRoutes/>
        </Col>
    )
};
