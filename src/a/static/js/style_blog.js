"use strict";

function main() {
    let css = document.getElementById("css");

    let preview_index = document.getElementById("preview-index");
    let preview_index_a = document.getElementById("preview-index-a");

    let preview_post = document.getElementById("preview-post");
    let preview_post_a = document.getElementById("preview-post-a");

    let minimal = document.getElementById("minimal");

    let data = new FormData();

    css.oninput = minimal.oninput = debounce(() => {
        data.set("style", css.value);

        fetch(`${window.location}/preview` + (minimal.checked ? "?minimal" : ""), {
            method: "POST",
            body: data,
        })
            .then((r) => r.json())
            .then((j) => {
                preview_index.src =
                    preview_index_a.href = `/blog/~preview?ctx=${j[0]}`;

                preview_post.src =
                    preview_post_a.href = `/blog/~preview?ctx=${j[1]}`;
            })
            .catch((e) => {
                console.error(e);
                alert(e);
            });
    }, 666);

    load_textarea_controls();

    css.oninput();
}

document.addEventListener("DOMContentLoaded", main);
