# OpenCraft Instance Manager Frontend

A single-page app(SPA) for the [OpenCraft Instance Manager (OCIM)](https://github.com/open-craft/opencraft).

## Running Locally

Run this outside the vagrant environment, but it is possible to run this frontend server within Vagrant during
development, for performance reasons it's better to run it separately outside of Vagrant instead. Also, use this
devstack as an independent React SPA.

- Install the API client:

```bash
./scripts/build-api-client.sh
```

- Install requirements:

```bash
npm install
```

- Run frontend:

```bash
npm start
```

- Generating New Components:

```bash
npm run generate # uses plop, more information here(https://plopjs.com/)
```

## API Client Instructions

- Updating the API Client:

```bash
cd ./frontend # go to frontend directory
npm run update-api-client
```

- Building the API Client:

```bash
cd ./frontend # go to frontend directory
npm run build-api-client
```

## Testing

- Running the tests and checks:

```bash
npm run lint # for running the linting

# for fixing the linting(it usually runs `--fix` flag with eslint so it tries to correct as many issues as possible but still can fail)
npm run lint-fix 

npm run test # for running the tests
```

## Deployment Process

The Deployment is done on automatically using CircleCI when any commit is added in the `stage` 
branch (for details, check `frontend-deploy` job in [circle.yml](../circle.yml)). The bundle is
hosted on S3 and is directly served from Cloudfront.

In case of production, the build is started when a tag is added matching the `/^release\-\w+\-\w+$/` regexp.

## Reuseable UI Components

A partial list of reusable UI components is shown in the `/demo` route, accessible in the development environment through [http://localhost:3000/demo](http://localhost:3000/demo).

## Frontend Architecture/Stack

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

When coding React components, please keep the following in mind:

* All components should subclass [`React.PureComponent`](https://reactjs.org/docs/react-api.html#reactpurecomponent).
* All component props and redux state variables that are complex objects should be immutable (enforced via TypeScript by declaring them as `ReadOnlyArray<T>`, `ReadOnlySet<T>`, and `ReadOnly<T>`, mutated using [`immutability-helper`](https://github.com/kolodny/immutability-helper) or plain ES6).
* Write sensible tests, including unit tests, [snapshot tests](https://jestjs.io/docs/en/snapshot-testing), and/or end-to-end tests.
    - When reviewing changes to snapshot tests, carefully review the HTML diff to ensure the changes are expected.
    - Test files should be located alongside the component they test (so `Card.tsx` is tested in `Card.spec.tsx`)    
    - Never import jest/test related code in `.ts` files that are part of the application (only in `.spec.tsx` files); this avoids adding several megabytes of test code to the app bundle.
    - When in doubt, end-to-end tests and Enzyme behavior tests are preferred. Snapshot tests are still useful, but not as important as an end to end test or even a regular React component test that simulates user interaction with the component and then make assertions about the result.
* Prefer to split big components up into smaller components that get composed together.
* Use the [Container Pattern](https://medium.freecodecamp.org/react-superpowers-container-pattern-20d664bdae65)
    - Don't write a `FoobarComponent` that loads `Foobar` data from the REST API then renders it; instead write a `FoobarComponent` that accepts `Foobar` data as a prop (so its props are never `undefined`), and then write a `FoobarContainerComponent` which loads the `Foobar` data from the REST API and then once it's loaded renders a `<FoobarComponent data={foobarData}/>`. This lets us test the presentation/UX separately from the API/backend, provides better separation of concerns, and reduces the need to write code that checks if the prop has data or not when rendering.
* Make sure the component is internationalized (see below) and accessible.
