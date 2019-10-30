const MODULES = ["auth", "ui", "registration"];
module.exports = function (plop) {
    // controller generator
    plop.setGenerator('component', {
        description: 'application component',
        prompts: [
            {
                type: 'input',
                name: 'name',
                message: 'component name'
            },
            {
                type: 'list',
                name: 'module',
                choices: MODULES,
                message: 'module in which to place component'
            }
        ],
        actions: [
            {
                type: 'add',
                path: 'src/{{module}}/components/{{name}}/{{name}}.tsx',
                templateFile: 'templates/component/component.tsx.hbs'
            },
            {
                type: 'add',
                path: 'src/{{module}}/components/{{name}}/{{name}}.spec.tsx',
                templateFile: 'templates/component/component.spec.tsx.hbs'
            },
            {
                type: 'add',
                path: 'src/{{module}}/components/{{name}}/index.ts',
                templateFile: 'templates/component/index.ts.hbs'
            },
            {
                type: 'add',
                path: 'src/{{module}}/components/{{name}}/styles.scss'
            },
            {
                type: 'add',
                path: 'src/{{module}}/components/{{name}}/displayMessages.ts',
                templateFile: 'templates/component/displayMessages.ts'
            },
            {
                type: 'append',
                path: 'src/{{module}}/components/index.ts',
                template: 'export * from "./{{name}}";\n'
            }
        ]
    });
};
