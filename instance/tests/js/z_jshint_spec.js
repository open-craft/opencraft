// Copyright (C) 2011 GitHub - Brandon Keepers (https://github.com/bkeepers)

// https://github.com/bkeepers/lucid/blob/master/spec/javascripts/lucid.aspects.spec.js

(function(){
"use strict";

// Tests //////////////////////////////////////////////////////////////////////

describe('JSHint', function () {
    var options = {curly: true, white: true, indent: 2},
    files = /^.*\/js\/src\/.*\.js$/;

    _.each(document.getElementsByTagName('script'), function (element) {
        var script = element.getAttribute('src');
        if (!files.test(script)) {
            return;
        }

        it(script, function () {
            console.log('Running JSHint on script: ' + script);
            var self = this;
            var source = jasmine.httpGET(script);
            var result = JSHINT(source, options);
            _.each(JSHINT.errors, function (error) {
                fail("line " + error.line + ' - ' + error.reason + ' - ' + error.evidence);
            });
            expect(true).toBe(true); // force spec to show up if there are no errors
        });

    });
});

})();
