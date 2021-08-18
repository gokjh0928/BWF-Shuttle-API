// Function that adds a spinner to display while loading
function loading() {
    var x = document.getElementById("content");
    if (x.style.display === "none") {
        x.style.display = "block";
    } else {
        x.style.display = "none";
    }
    var y = document.getElementById("loading");
    if (y.style.display === "none") {
        y.style.display = "block";
    }
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