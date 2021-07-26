# Developing the console frontend

## Using a different backend

If you only want to make changes to the console frontend
(or don't have credentials for running a functional backend),
you can point your devserver at a deployed environment (usually `stage`):

    REACT_APP_OCIM_API_BASE=https://stage.manage.opencraft.com npm start

However, if you then try to access the frontend at `localhost`, you'll
run into CORS issues.
To avoid those, add an entry to your `/etc/hosts` file:

    127.0.0.1 localhost.opencraft.com

You can then access the devserver at http://localhost.opencraft.com:3000.
