"use strict";

function main() {
    let css = document.getElementById("css");

    let preview_index = document.getElementById("preview-index");
    let preview_index_a = document.getElementById("preview-index-a");

    let preview_post = document.getElementById("preview-post");
    let preview_post_a = document.getElementById("preview-post-a");

    css.oninput = debounce(() => {
        preview_index.src = preview_index_a.href = `${window.location}/preview/index?style=${encodeURIComponent(css.value)}`;
        preview_post.src = preview_post_a.href = `${window.location}/preview/post?style=${encodeURIComponent(css.value)}`;
    }, 555);

    load_textarea_controls();

    css.oninput()
}

document.addEventListener("DOMContentLoaded", main);
