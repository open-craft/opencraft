import * as React from 'react';
import { ContentPage } from 'ui/components';
import './styles.scss';

export const FaqPage: React.FC = () => (
    <ContentPage
    title="FAQ"
    subtitle="Frequently Asked Questions"
  >
    <div className="faq-container">

        <h4>
            I’m new to the Open edX platform. Where can I start?
        </h4>
        <p>
            Open edX has excellent and well-maintained official documentation. You will find all you need to know about how to build and run courses in the doc.
        </p>
        <p>
            We also encourage course authors to take edX's Course Creator courses, which show how to design, develop, and run online courses on the Open edX platform following best practices. We’re also happy to give you a quick tour of the platform or answer specific questions - simply contact us.
        </p>

        <h4>
            What release of the Open edX platform do you use?
        </h4>
        <p>
            We always use the latest version, and automatically upgrade all of our hosted instances in the weeks following a release. Version upgrades, maintenance and major fixes are included in the subscription fee for all of our hosting plans.
        </p>
        <p>
            Using the latest version provides unparalleled advantages to our users in matters of features, performance and security.
        </p>

        <h4>
            What functionalities are included in your hosting plans?
        </h4>
        <p>
        Users of our Pro & Teacher hosting plan get access to a full-featured, dedicated Open edX instance that includes the Open edX LMS and Studio authoring tool. See this PDF document for a full feature comparison of our hosting plans.
        </p>

    </div>
  </ContentPage>
);