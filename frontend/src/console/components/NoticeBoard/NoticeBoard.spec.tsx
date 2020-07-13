import React from 'react';

import { OpenEdXInstanceDeploymentStatusStatusEnum as DeploymentStatus } from 'ocim-client';
import { setupComponentForTesting } from 'utils/testing';

import { NoticeBoard } from './NoticeBoard'


it('Renders all notification types without crashing', () => {
  const deployedChanges = [
    [
      'change',
      'some_var1',
      [
        'test',
        'test1'
      ]
    ],
    [
      'change',
      'theme_config.btn-secondary-bg',
      [
        '#000000',
        '#FFFFFF'
      ]
    ],
    [
      'add',
      'theme_config',
      [
        [
          'added-bg',
          '#FFFFFF'
        ]
      ]
    ],
    [
      'remove',
      'theme_config',
      [
        [
          'removed-bg',
          '#FFFFFF'
        ]
      ]
    ],
    [
      'add',
      'static_content_overrides',
      [
        [
          'version',
          0
        ],
        [
          'homepage_overlay_html',
          '<h1>Welcome to Wonderland</h1><p>It works! Powered by Open edX®</p>'
        ]
      ]
    ],
    [
      'change',
      'some_dict.version',
      [
        0,
        1
      ]
    ],
    [
      'add',
      '',
      [
        [
          'instance_name',
          'Wonderland'
        ]
      ]
    ],
    [
      'remove',
      '',
      [
        [
          'some_var2',
          'test'
        ]
      ]
    ]
  ];
  const date = new Date('2020-06-13T15:07:05.158Z');

  const notifications = Object.values(DeploymentStatus).map(status => ({
    status, date, deployedChanges
  }));

  const tree = setupComponentForTesting(
    <NoticeBoard />,
    {
      console: {
        loading: false,
        activeInstance: {
          data: {
            id: 1,
            instanceName: "test",
            subdomain: "test",
            lmsUrl: "test-url",
            studioUrl: "test-url",
            isEmailVerified: true,
          },
          deployment: {
            status: "preparing",
            undeployedChanges: [],
            deployedChanges: null,
            type: 'admin',
          }
        },
        instances: [{
          id: 1,
          instanceName: "test",
          subdomain: "test",
        }],
        notifications: notifications,
        notificationsLoading: false
      }
    }
  ).toJSON();

  expect(tree).toMatchSnapshot();
});
