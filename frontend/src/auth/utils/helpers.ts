import { V2Api } from 'global/api';


export const checkAuthAndRefreshToken = async () => {
  let refreshToken = localStorage.getItem('token_refresh');
  let response = null;
  let isAuthenticated = false;

  if (refreshToken) {
    response = await V2Api.authRefreshCreate({data: {refresh: refreshToken}});
  }

  if (response){
    console.log(response)
  }

  return isAuthenticated;
}
