
var apigClient = apigClientFactory.newClient();

function chatBotResponse() {
  
  lastUserMessage = userMessage();

  return new Promise(function(resolve,reject){

    var body = {
      "message": lastUserMessage,
      "userId": "lf0"
    };

    //console.log(body)
    var params = {};
    var additionalParams = {};

    apigClient.chatbotPost(params, body, additionalParams)
    .then(function (result) {
      // Add success callback code here.
      
      //console.log(result);
      response = result.data.body.message;

      console.log(response);

      // shouldScroll = messages.scrollTop + messages.clientHeight === messages.scrollHeight;
      
      //${response['message']}
      setTimeout(function () {
        outputArea.append(`
          <div class='user-message'>
            <div class='message'>
            ${response}
            </div>
          </div>
        `);
      }, 250);
      
      // if (!shouldScroll) {
      //   scrollToBottom();
      // }

      resolve("done");
      
    }).catch(function (result) {
      // Add error callback code here.
      console.log("Rejected");
      reject("Rejected");
    });

  });

}

function userMessage() {

  var message = $("#user-input").val();
  console.log(message);

  outputArea.append(`
    <div class='bot-message'>
      <div class='message'>
        ${message}
      </div>
    </div>
  `);
  return message;

}

//JS Code
function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

const messages = document.getElementById('chat-output');

//scrollToBottom();

var outputArea = $("#chat-output");

$("#user-input-form").on("submit", function (e) {
  chatBotResponse();  
  $("#user-input").val("");

});

$(window).on('keydown', function(e) {
  if (e.which == 13) {

    chatBotResponse();
    $("#user-input").val("");
    return false;
  }
});
