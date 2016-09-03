$("#overview_0").click(function() {
	console.log("something happened");
    $('#full').animate({
        scrollTop: $("#full_0").offset().top
    }, 2000);
});

$("#overview_1").click(function() {
    $('html, body').animate({
        scrollTop: $("#full_1").offset().top
    }, 2000);
});

$("#overview_2").click(function() {
    $('html, body').animate({
        scrollTop: $("full_2").offset().top
    }, 2000);
});

$("#overview_3").click(function() {
    $('html, body').animate({
        scrollTop: $("#full_3").offset().top
    }, 2000);
});

$("#overview_4").click(function() {
    $('html, body').animate({
        scrollTop: $("#full_4").offset().top
    }, 2000);
});