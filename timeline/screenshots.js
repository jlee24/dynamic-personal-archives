var fs = require('fs');
var system = require('system');
var args = system.args;

var idx = Number(args[1]);
var url = args[2];

console.log("idx/url", idx, url);

var page = require("webpage").create();

// Let's be an iPhone!
page.settings.userAgent = "Mozilla/5.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit/600.1.3 (KHTML, like Gecko) Version/8.0 Mobile/12A4345d Safari/600.1.4";
page.settings.localToRemoteUrlAccessEnabled = true;
//page.settings.resourceTimeout = 400;

page.viewportSize = {width: 375, height: 627};

page.open(url, function() {

    console.log("open", idx);

    setTimeout(function() {

	console.log("render", idx);

	page.render("images/archive-" + idx + ".jpg");

	phantom.exit();
    }, 4000);

});
