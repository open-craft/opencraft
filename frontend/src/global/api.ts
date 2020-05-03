import { OCIM_API_BASE } from 'global/constants';
import { V2Api as _V2Api, Configuration } from 'ocim-client';
import { performLogout } from 'auth/actions';

const config = new Configuration({
  basePath: `${OCIM_API_BASE}/api`,
  apiKey: (name: string, scopes?: string[]) => {
    const authToken = localStorage.getItem('token_access');
    // The current version of the API client requires us to specify the word "Bearer"
    // The previous version did not.
    return authToken ? `Bearer ${authToken}` : '';
  },
  middleware: [
    {
      post: async (context) => {
        if (context.response.status === 403) {
          // Failed requests return 403 and mean that the access token is
          // expired, so we trigger a page refresh.
          window.location.reload(false);
        } else if (context.response.status === 401) {
          // If the refresh endpoint fails, it means that the refresh
          // is expired, and the user is effectively logged out.
          performLogout();
        }
        return context.response;
      }
    }
  ]
});

export const V2Api = new _V2Api(config);

if (process.env.NODE_ENV === 'development') {
  // For development and debugging purposes, expose the API client to the browser console.
  (window as any).V2Api = V2Api;
}
