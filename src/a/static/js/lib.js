"use strict";

function debounce(func, delay) {
    let d;

    return function () {
        let context = this;
        let args = arguments;
        clearTimeout(d);
        d = setTimeout(() => func.apply(context, args), delay);
    };
}

function load_textarea_controls() {
    document.querySelectorAll("textarea,input").forEach((textarea) => {
        textarea.onkeydown = (e) => {
            if (e.key !== "Tab") return;

            let end = textarea.selectionEnd;
            let text = textarea.value;

            let tab = "    ";

            textarea.value =
                text.substring(0, textarea.selectionStart) +
                tab +
                text.substring(end);

            textarea.selectionEnd = end + tab.length;

            e.preventDefault();
        };
    });
}

