
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('categories').addEventListener('change', function () {
        var categoryNames = {
            "MS": "Mens Singles",
            "WS": "Womens Singles",
            "MD": "Mens Doubles",
            "WD": "Womens Doubles",
            "XD": "Mixed Doubles"
        }
        if (this.value != "Choose...") {
            for (let i = 0; i < document.getElementsByClassName('category-text').length; i++) {
                if (i % 2 == 0) {
                    document.getElementsByClassName('category-text')[i].innerHTML = categoryNames[this.value];
                }
                else {
                    document.getElementsByClassName('category-text')[i].innerHTML = this.value;
                }
            }
        }
        else {
            for (text of document.getElementsByClassName('category-text')) {
                text.innerHTML = '{category}';
            }
        }
    });
});



document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('weeks').addEventListener('change', function () {
        if (this.value != "Choose...") {
            let yearVal = this.value.split('-')[0];
            let weekVal = this.value.split('-')[1];
            for (let i = 0; i < document.getElementsByClassName('yw-text').length; i++) {
                if (i % 2 == 0) {
                    document.getElementsByClassName('yw-text')[i].innerHTML = yearVal;
                }
                else {
                    document.getElementsByClassName('yw-text')[i].innerHTML = weekVal;
                }
            }
        }
        else {
            for (let i = 0; i < document.getElementsByClassName('yw-text').length; i++) {
                if (i % 2 == 0) {
                    document.getElementsByClassName('yw-text')[i].innerHTML = '{year}';
                }
                else {
                    document.getElementsByClassName('yw-text')[i].innerHTML = '{week}';
                }
            }
        }
    });
});


document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('dates').addEventListener('change', function () {
        let emptyDates = ['{year}', '{month}', '{day}']
        if (this.value != "Choose...") {
            for (let i = 0; i <= 2; i++) {
                document.getElementsByClassName('ymd-text')[i].innerHTML = this.value.split('/')[i];
                document.getElementsByClassName('ymd-text')[i + 3].innerHTML = this.value.split('/')[i];
            }
        }
        else {
            for (let i = 0; i <= 2; i++) {
                document.getElementsByClassName('ymd-text')[i].innerHTML = emptyDates[i];
                document.getElementsByClassName('ymd-text')[i + 3].innerHTML = emptyDates[i];
            }
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('num-rows').addEventListener('keyup', function () {
        if (this.value != '') {
            for (text of document.getElementsByClassName('rows-text')) {
                text.innerHTML = this.value;
            }
        }
        else {
            for (text of document.getElementsByClassName('rows-text')) {
                text.innerHTML = "{rows}";
            }
        }
    });
});

document.addEventListener('DOMContentLoaded', () => {
    var max_chars = 4;
    document.getElementById('ranking-rows').addEventListener('input', function () {
        if ($(this).val().length >= max_chars) {
            $(this).val($(this).val().substr(0, max_chars));
        }
    });
});


// Function that adds a spinner to display while loading
function loading(text) {
    document.getElementById("content").classList.add("loading");
    document.getElementById("loading").classList.remove("loading");
    if (text || text.length > 0) {
        document.getElementById("loading-text").innerHTML = text;
    }
    
}

// Function that adds a spinner to display while loading
function downloading() {
    document.getElementById("downloading").classList.remove("loading");
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

