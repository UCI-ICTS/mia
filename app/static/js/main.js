var ChatApp = {
    SCRIPT_ROOT: '',
    initialize: function(scriptRoot) {
        this.SCRIPT_ROOT = scriptRoot;
        this.bindEvents();
    },
    bindEvents: function() {
        $(document).on('click', 'button.response', this.onButtonClick.bind(this));
        $(document).on('change', "#checkbox-form input[type='checkbox'], #child-ages-checkbox-form input[type='checkbox']", this.onCheckboxChange.bind(this));
        $('.user-response-container').on('submit', '#checkbox-form', this.onFamilyEnrollmentForm.bind(this));
        $('.user-response-container').on('submit', '#child-ages-checkbox-form', this.onChildAgeEnrollmentForm.bind(this));
        $('.user-response-container').on('keyup change', '#firstname, #lastname', this.onCheckInputs.bind(this));
        $(window).on('resize', this.adjustChatWindowHeight.bind(this));
        $('.user-response-container').on('submit', '#contact-other-adult-form', this.onSubmitContactAnotherAdultForm.bind(this));
        $('.user-response-container').on('click', '#skip-button', this.onSkipContactAnotherAdultForm.bind(this));
    },
    smoothScrollToBottom: function() {
        const chatWindow = document.getElementById('chat-window');
        chatWindow.scrollTop = chatWindow.scrollHeight;
    },
    onButtonClick: function(event) {
        event.preventDefault();
        var that = this; // store reference to the ChatApp object
        var chatWindow = document.getElementById("chat-window");
        var uuid = that.getInviteUuid();
        $.getJSON(this.SCRIPT_ROOT + '/invite/' + uuid + '/user_response', {
            id: event.target.id // event object to access the button clicked
        }, function(data) {
            that.processChatMessages(data)
        });
    },
    onCheckboxChange: function() {
        let oneChecked = false;
        $("#checkbox-form input[type='checkbox'], #child-ages-checkbox-form input[type='checkbox']").each(function() {
            if ($(this).prop('checked')) oneChecked = true;
        });
        $('#submit-button').prop('disabled', !oneChecked);
    },
    onFamilyEnrollmentForm: function(event) {
        event.preventDefault();
        var that = this; // store reference to the ChatApp object
        var uuid = that.getInviteUuid();
        var formData = $(event.target).serialize();
        $.post(this.SCRIPT_ROOT + '/invite/' + uuid + '/family_enrollment_form', formData, function(data) {
            data.echo_user_response = data.echo_user_response.join(', ');
            that.processChatMessages(data)
        });
    },
    onChildAgeEnrollmentForm: function(event) {
        event.preventDefault();
        var that = this; // store reference to the ChatApp object
        var uuid = that.getInviteUuid();
        var formData = $(event.target).serialize();
        $.post(this.SCRIPT_ROOT + '/invite/' + uuid + '/child_age_enrollment_form', formData, function(data) {
            data.echo_user_response = data.echo_user_response.join(', ');
            that.processChatMessages(data)
        });
    },
    onCheckInputs: function() {
        let firstname = $('#firstname').val().trim();
        let lastname = $('#lastname').val().trim();
        if (firstname !== "" && lastname !== "") {
            $('#submit-button').prop('disabled', false);
        } else {
            $('#submit-button').prop('disabled', true);
        }
    },
    onSubmitContactAnotherAdultForm: function(event) {
        event.preventDefault();
        var that = this; // store reference to the ChatApp object
        var uuid = that.getInviteUuid();
        var formData = $(event.target).serialize() + "&submit=true";
        $.post(this.SCRIPT_ROOT + '/invite/' + uuid + '/contact_another_adult_form', formData, function(data) {
            that.processChatMessages(data)
        });
    },
    onSkipContactAnotherAdultForm: function(event) {
        event.preventDefault();
        var that = this; // store reference to the ChatApp object
        var uuid = that.getInviteUuid();
        var formData = $('#contact-other-adult-form').serialize() + "&submit=false";
        $.post(this.SCRIPT_ROOT + '/invite/' + uuid + '/contact_another_adult_form', formData, function(data) {
            that.processChatMessages(data)
        });
    },
    processChatMessages: function(data) {
        // --- echo the response from the user in the chat window
        var new_user_content = `
            <div class="message-row user">
                <div class="message-content user">
                    <span>${data.echo_user_response}</span>
                </div>
            </div>`;
        var chat = document.getElementById("chat-window");
        chat.innerHTML += new_user_content;
        this.smoothScrollToBottom();

        // --- return the next chatbot message
        var botMessages = data.next_sequence.bot_messages;
        for (var i = 0; i < botMessages.length; i++) {
            var new_bot_content = `
                <div class="message-row bot">
                    <div class="message-content bot">
                        <span>${botMessages[i]}</span>
                    </div>
                </div>`;
            chat.innerHTML += new_bot_content;
            this.smoothScrollToBottom();
        }
        if (data.next_sequence.bot_html_type == 'image') {
            var imagePath = SCRIPT_ROOT + "/static/images/" + data.next_sequence.bot_html_content;
            var imgElement = `<img src="${imagePath}" alt="${data.next_sequence.bot_html_content}">`;

            var new_bot_image_content = `
                <div class="message-row bot">
                    <div class="message-content bot">
                        <span>${imgElement}</span>
                    </div>
                </div>`;
            chat.innerHTML += new_bot_image_content;
            this.smoothScrollToBottom();
        }
        if (data.next_sequence.bot_html_type == 'video') {
            var videoElement = `<iframe width="100%" height="315" src="${data.next_sequence.bot_html_content}" frameborder="0" allowfullscreen></iframe>`;

            var new_bot_video_content = `
                <div class="message-row bot">
                    <div class="message-content bot">
                        <span>${videoElement}</span>
                    </div>
                </div>`;
            chat.innerHTML += new_bot_video_content;
            this.smoothScrollToBottom();
        }

        // --- configure form or buttons for the next user response
        if (data.next_sequence.user_html_type == 'form') {
            // --- set the form for the next user response
            var responseContainer = document.querySelector('.user-response-button-group');
            responseContainer.innerHTML = data.next_sequence.user_responses[0][1];
        } else {
            // --- set the buttons for the next user response
            var buttonDiv = document.getElementById("user-response-button-group");
            var userResponses = data.next_sequence.user_responses;
            buttonDiv.innerHTML = "";

            for (var i = 0; i < userResponses.length; i++) {
                var button = document.createElement('button');
                button.textContent = userResponses[i][1];
                button.className = "response user-response-button";
                button.id = userResponses[i][0];
                buttonDiv.appendChild(button);
            }
        }
        this.adjustChatWindowHeight();
    },
    adjustChatWindowHeight: function() {
        var windowHeight = $(window).height();
        var formContainerHeight = $('.user-response-container').outerHeight(true);
        var otherHeight = 90; // the height of other elements, adjust as needed
        var newChatWindowHeight = windowHeight - formContainerHeight - otherHeight;

        $('#chat-window').css('height', newChatWindowHeight + 'px');
        this.smoothScrollToBottom();
    },
    getInviteUuid: function() {
        let currentPath = window.location.pathname;
        let pathParts = currentPath.split('/');
        let uuid = pathParts[pathParts.length - 2];
        return uuid;
    },
};

