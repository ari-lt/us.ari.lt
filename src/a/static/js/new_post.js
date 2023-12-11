"use strict";

function main() {
    let content = document.getElementById("content");
    let preview = document.getElementById("preview");
    let preview_a = document.getElementById("preview-a");
    let title = document.getElementById("title");

    let data = new FormData();

    content.oninput = title.oninput = debounce(() => {
        data.set("content", content.value);
        data.set("title", title.value);

        fetch(`${window.location}/preview`, {
            method: "POST",
            body: data,
        })
            .then(r => r.json())
            .then((j) => preview.src = preview_a.href = `/blog/~preview?ctx=${j[0]}`)
            .catch((e) => {
                console.error(e);
                alert(e);
            });
    }, 666);

    load_textarea_controls();

    content.oninput();
}

document.addEventListener("DOMContentLoaded", main);
