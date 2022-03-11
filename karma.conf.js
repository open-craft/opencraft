// Karma configuration
// Generated on Thu Apr 11 2019 16:33:58 GMT-0500 (Central Daylight Time)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine', 'fixture'],


    // list of files / patterns to load in the browser
    files: [
      'static/external/js/jquery.min.js',
      'static/external/js/underscore-min.js',
      'static/external/js/angular.min.js',
      'static/external/js/angular-route.min.js',
      'static/external/js/angular-ui-router.min.js',
      'static/external/js/angular-sanitize.min.js',
      'static/external/js/angucomplete-alt.min.js',
      'static/external/js/marked.min.js',
      'static/js/dist/angular-foundation-tpls.js',
      'static/external/js/restangular.min.js',
      'static/external/js/angular-mocks.js',
      'static/external/js/jshint.js',
      'static/external/js/icheck.min.js',
      'instance/static/js/src/**/*.js',
      'registration/static/js/src/**/*.js',
      'instance/tests/fixtures/**/*.json',
      'instance/static/html/instance/**/*.html',
      'instance/tests/js/**/*spec.js',
      'registration/tests/js/**/*spec.js',
    ],


    // list of files / patterns to exclude
    exclude: [
    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      '**/*.json': ['json_fixtures'],
      '**/*.html': ['html2js'],
      'instance/static/js/src/**/*.js': ['coverage'],
      'registration/static/js/src/**/*.js': ['coverage'],
    },

    plugins: [
        'karma-fixture',
        'karma-firefox-launcher',
        'karma-jasmine',
        'karma-json-fixtures-preprocessor',
        'karma-html2js-preprocessor',
        'karma-jasmine-html-reporter',
        'karma-coverage',
    ],
    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress', 'coverage'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['FirefoxHeadless'],
    customLaunchers: {
        'FirefoxHeadless': {
            base: 'Firefox',
            flags: [
                '-headless',
            ]
        }
    },

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,

    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: Infinity,

    jsonFixturesPreprocessor: {
      variableName: '__json__'
    },

    coverageReporter: {
        reporters: [
            {
                type: 'text',
                dir: 'coverage/',
                subdir: 'text',
                file: 'coverage.txt',
            },
            {
                type: 'lcov',
                dir: 'coverage/',
                subdir: 'lcovonly',
            },
        ],
        check: {
            global: {
                statements: 70,
                branches: 50
            }
        }
    }

  })
}
