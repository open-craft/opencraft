import React from 'react';
import { Container } from 'react-bootstrap';
import { useMatomo } from '@datapunt/matomo-tracker-react';
import { useHistory } from 'react-router';
import { Footer, Header, Main } from '..';
import './styles.scss';

export const App: React.FC = () => {
  const { trackPageView } = useMatomo();
  React.useEffect(() => {
    trackPageView({});
  }, [trackPageView]);

  const history = useHistory();
  React.useEffect(() => {
    return history.listen(location => {
      trackPageView({});
    });
  }, [trackPageView, history]);
  return (
    <Container fluid className="app-container">
      <Header />
      <Main />
      <Footer />
    </Container>
  );
};
