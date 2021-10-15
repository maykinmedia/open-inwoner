import {getEditor} from "./editor";


const SELECTOR = '.ckeditor-selection';

const nodes = document.querySelectorAll(SELECTOR);

for (const node of nodes) {
    getEditor(node);
}
