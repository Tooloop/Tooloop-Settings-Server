var TooloopUI = function () {};


TooloopUI.toggleMenu = function() {
    $('body').toggleClass('mobile-menu');
    $('#sidebar').toggleClass('mobile-menu');
}


TooloopUI.showCover = function() {
    if(!$('#cover').length) {
        $('body').append('<div id="cover"></div>');
    }
    var cover = $('#cover');
    cover.fadeIn(100);
    return cover;
}


TooloopUI.hideCover = function() {
    $('#cover').fadeOut(200);
}


// // -------------------------------------------------------------------------
// // FEEDBACK
// // -------------------------------------------------------------------------
// TooloopUI.feedbackTimeouts = {};

// TooloopUI.attachFeedback = function(form) {    
//     var feedbackId = form.id+"-feedback";

//     // check if there already is a feedback container
//     if ($("#"+feedbackId).length > 0) {
//         // cancel fade out
//         clearTimeout(feedbackTimeouts[feedbackId]);
//         return $("#"+feedbackId);
//     }

//     // add html
//     $(form).append('\
//         <div id="'+form.id+'-feedback" class="feedback" style="display:block;"> \
//             <img class="feedback-icon" src="static/img/waiting_animation.gif" style="vertical-align: middle; height: 1.777777em; margin-right: -0.233333em;" /> \
//             <label class="feedback-text" style="display:none;"></label> \
//         </div> \
//     ');

//     return $("#"+feedbackId);
// }

// TooloopUI.displayConfirmFeedback = function(feedbackContainer, message) {
//     displayFeedback(feedbackContainer, "static/img/confirm_animation.gif", message);
// }

// TooloopUI.displayErrorFeedback = function(feedbackContainer, message) {
//     displayFeedback(feedbackContainer, "static/img/error_animation.gif", message);
// }

// TooloopUI.displayFeedback = function(feedbackContainer, icon, message) {
//     feedbackContainer.children(".feedback-icon").attr("src", icon);
//     feedbackContainer.children(".feedback-text").text(message);
//     feedbackContainer.children(".feedback-text").delay(400).fadeIn(500);

//     // remove feedback
//     feedbackTimeouts[feedbackContainer.attr("id")] = setTimeout(function(){
//         feedbackContainer.fadeOut(400, function(){
//             feedbackContainer.remove();
//         });
//     }, 3000);
// }