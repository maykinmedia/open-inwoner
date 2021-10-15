import {getEditor} from "./editor";


const SELECTOR = '.ckeditor-selection';

const nodes = document.querySelectorAll(SELECTOR);

for (const node of nodes) {
    console.log(node);
    // const props = node.dataset;
    // ReactDOM.render(<AlfrescoDocumentSelection {...props} />, node);
    getEditor(node);
}
