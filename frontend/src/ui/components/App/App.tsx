import React from 'react';
import { Container } from 'react-bootstrap';
import { Footer, Header, Main } from '..';
import './styles.scss';

export const App: React.FC = () => (
  <Container fluid className="app-container">
    <Header/>
    <Main />
    <Footer />
  </Container>
);
