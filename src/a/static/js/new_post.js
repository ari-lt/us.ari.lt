"use strict";

function main() {
    let content = document.getElementById("content");
    let preview = document.getElementById("preview");
    let preview_a = document.getElementById("preview-a");
    let title = document.getElementById("title");

    content.oninput = title.oninput = debounce(() => {
        preview.src = preview_a.href = `${
            window.location
        }/preview?content=${encodeURIComponent(
            content.value,
        )}&title=${encodeURIComponent(title.value)}`;
    }, 555);

    load_textarea_controls();

    content.oninput();
}

document.addEventListener("DOMContentLoaded", main);
