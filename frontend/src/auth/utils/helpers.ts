import { V2Api } from 'global/api';

export const checkAuthAndRefreshToken = async () => {
  const refreshToken = localStorage.getItem('token_refresh');
  let response = null;

  if (refreshToken) {
    try {
      response = await V2Api.authRefreshCreate({
        data: { refresh: refreshToken }
      });
    } catch (e) {
      return false;
    }
  }

  if (response) {
    localStorage.setItem('token_access', response.access);
    return true;
  }

  return false;
};
