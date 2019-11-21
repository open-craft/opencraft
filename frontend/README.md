# OpenCraft Instance Manager Frontend

A single-page app for the [OpenCraft Instance Manager (OCIM)](https://github.com/open-craft/opencraft).

# Running with Vagrant

While it is possible to run this frontend server within Vagrant during 
development, for performance reasons it's better to run it separately 
outside of Vagrant instead. 


# Frontend Architecture/Stack

We use React, TypeScript, Bootstrap, and SCSS for the frontend.

For global state shared among different parts of the application, we use Redux. 
So things like the user's login/logout status, the user's details etc. should 
be kept in the Redux state and modified using actions.

For all other state, such as data required just for a particular 
widget/component/page, we just use "normal" React props/state; this is because 
Redux imposes a lot of boilerplate code overhead and offers little value if the 
state is not shared among diverse parts of the application.

However, just because we use React and, when necessary, Redux, this doesn't mean
all the code has to be inside React components or the Redux store; "regular" 
JavaScript code launched from main.tsx that for example talks to the Redux 
store is always an option. 

## React Component Guidelines

Besides the general [coding standards](https://handbook.opencraft.com/en/latest/coding_standards/#coding-standards) in the OpenCraft handbook, there are [React specific tips](https://doc.opencraft.com/en/latest/coding-best-practices/#reactjs) in our tech repo. Please follow them when developing on the Ocim frontend.
