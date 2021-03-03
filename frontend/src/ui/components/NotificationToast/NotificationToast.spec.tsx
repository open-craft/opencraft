import React from 'react';
import { setupComponentForTesting } from "utils/testing";
import { NotificationToast } from './NotificationToast';

it('renders without crashing', () => {
    const messages = {
        notificationBody: {
            defaultMessage:
              'Your updates are being published to your live site (LMS) ' +
              'This can take 2 - 3 hours.',
            description: 'Text for the toast notification on clicking Publish'
          },
          notificationHelp: {
            defaultMessage: 'Close notification.',
            description: 'Helper text for closing the toast notification'
          }
    }

    const tree = setupComponentForTesting(<NotificationToast
        show={false}
        onClose={()=>{}}
        delay={4000}
        autohide
        bodyMessageId="notificationBody"
        closeMessage={messages.notificationHelp.defaultMessage}
        messages={messages}
    />).toJSON();
    expect(tree).toMatchSnapshot();
});
