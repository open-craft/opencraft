import { ROUTES } from 'global/constants';
import * as React from 'react';
import { NavLink } from 'react-router-dom';
import './style.scss';

interface Props {}

export const CustomDomainContactPage: React.FC<Props> = (props: Props) => {
  return (
    <div className="custom-domain-contact-page">
      <h1>Custom Domain</h1>
      <div className="custom-domain-contact-inner">
        <p>
          To use custom domain, please contact us at&nbsp;
          <a href="mailto:contact@opencraft.com">contact@opencraft.com</a>
        </p>
        <NavLink className="nav-link back-link" to={ROUTES.Registration.HOME}>
          Go back
        </NavLink>
      </div>
    </div>
  );
};
