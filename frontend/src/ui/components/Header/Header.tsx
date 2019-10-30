import logo from 'assets/icons.svg';
import * as React from 'react';
import { Col, Row } from 'react-bootstrap';
import './styles.scss'

export const Header: React.FC = () => (
    <Row as="header" className="app-header">
        <Col lg>

        </Col>
        <Col lg>
            <svg>
                <use xlinkHref={logo + "#opencraft_logo"}/>
            </svg>
        </Col>
        <Col lg>

        </Col>
    </Row>
);
