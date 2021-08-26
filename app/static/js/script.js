// Function that adds a spinner to display while loading
function loading() {
    document.getElementById("content").classList.add("loading");
    document.getElementById("loading").classList.remove("loading");
}

(function () {
    'use strict';
    window.addEventListener('load', function () {
        // Fetch all the forms we want to apply custom Bootstrap validation styles to
        var forms = document.getElementsByClassName('needs-validation');
        // Loop over them and prevent submission
        var validation = Array.prototype.filter.call(forms, function (form) {
            form.addEventListener('submit', function (event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();

$('#psw, #psw-repeat').on('keyup', function () {
    if ($('#psw').val() && $('#psw-repeat').val()) {
        if ($('#psw').val() != $('#psw-repeat').val()) {
            $('#message').css('display', 'block');
            $('#message').html('Passwords Not Matching').css('color', 'red');
        }
        else {
            $('#message').html('Passwords Matching').css('color', 'green');
        }
    }
    else {
        $('#message').css('display', 'None');
    }
});