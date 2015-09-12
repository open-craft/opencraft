// Copyright (C) 2011 GitHub - Brandon Keepers (https://github.com/bkeepers)

// https://github.com/bkeepers/lucid/blob/master/spec/javascripts/lucid.aspects.spec.js

"use strict";

// Tests //////////////////////////////////////////////////////////////////////

describe('JSHint', function () {
    var options = {curly: true, white: true, indent: 2},
    files = /^.*\/js\/src\/.*\.js$/;

    function get(path) {
        path = path + "?" + new Date().getTime();

        var xhr;
        try {
            xhr = new XMLHttpRequest();
            xhr.open("GET", path, false);
            xhr.send(null);
        } catch (e) {
            throw new Error("couldn't fetch " + path + ": " + e);
        }
        if (xhr.status < 200 || xhr.status > 299) {
            throw new Error("Could not load '" + path + "'.");
        }

        return xhr.responseText;
    }

    _.each(document.getElementsByTagName('script'), function (element) {
        var script = element.getAttribute('src');
        if (!files.test(script)) {
            return;
        }

        console.log('Running JSHint on script: ' + script);
        it(script, function () {
            var self = this;
            var source = get(script);
            var result = JSHINT(source, options);
            _.each(JSHINT.errors, function (error) {
                fail("line " + error.line + ' - ' + error.reason + ' - ' + error.evidence);
            });
            expect(true).toBe(true); // force spec to show up if there are no errors
        });

    });
});
