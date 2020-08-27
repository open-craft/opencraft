import React, { ReactNode } from 'react';
import {
  createInstance,
  MatomoProvider,
  useMatomo
} from '@datapunt/matomo-tracker-react';
import {
  MATOMO_ALIAS_DOMAIN,
  MATOMO_BASE_URL,
  MATOMO_MY_DOMAIN,
  MATOMO_SITE_ID
} from '../global/constants';

interface MatomoTrackerProps {
  children: ReactNode;
}

interface MatomoAdditionalConfiguration {
  [propName: string]: any;
}

interface MatomoConfiguration {
  urlBase: string;
  siteId: number;
  configurations?: MatomoAdditionalConfiguration;
}

interface MatomoUserIdTrackerProps {
  userId: string;
}

/*
 * This wrapper component initializes the Matomo tracking by wrapping the children
 * elements, if the tracking is enabled by providing a valid value for the 'MATOMO_BASE_URL'
 * constant. It allows tracking page views, events and the user id, when available.
 *
 * The 'MATOMO_ALIAS_DOMAIN' constant allows the cross-domain linking of another site with
 * this site so that they are treated as the same site in Matomo.
 */
export const MatomoTracker: React.FC<MatomoTrackerProps> = (
  props: MatomoTrackerProps
) => {
  let element = props.children;
  if (MATOMO_BASE_URL) {
    const matomoConfiguration: MatomoConfiguration = {
      urlBase: MATOMO_BASE_URL,
      siteId: parseInt(MATOMO_SITE_ID, 10)
    };
    if (MATOMO_ALIAS_DOMAIN) {
      const myDomain = `*.${MATOMO_MY_DOMAIN}`;
      const aliasDomain = `*.${MATOMO_ALIAS_DOMAIN}`;
      matomoConfiguration.configurations = {
        enableCrossDomainLinking: true,
        setDomains: [myDomain, aliasDomain]
      };
    }
    element = (
      <MatomoProvider value={createInstance(matomoConfiguration)}>
        {props.children}
      </MatomoProvider>
    );
  }
  return <>{element}</>;
};

/**
 * This is a component passes the provided user id to Matomo if Matomo tracking is enabled.
 * The 'pushInstruction' function exposed by the 'useMatomo()' hook is used to do this.
 *
 * This component is needed as all the components in the registration process are classes and hence
 * the 'yseMatomo' hook cannot be directly used in those components.
 */
export const MatomoUserIdTracker: React.FC<MatomoUserIdTrackerProps> = (
  props: MatomoUserIdTrackerProps
) => {
  const { pushInstruction } = useMatomo();
  if (MATOMO_BASE_URL && props.userId) {
    pushInstruction('setUserId', props.userId);
  }
  return null;
};
