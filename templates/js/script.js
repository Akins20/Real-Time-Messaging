var socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('message', function(data) {
    var messageList = document.getElementById('messages');
    var messageItem = document.createElement('li');
    messageItem.innerHTML = data.message;
    messageList.appendChild(messageItem);
});

function sendMessage() {
    var messageInput = document.getElementById('message_input');
    var message = messageInput.value;
    socket.emit('message', { message: message });
    messageInput.value = '';
}