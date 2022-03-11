class MessageFile {
    constructor(node) {
        this.node = node;
        this.fileInput = node.querySelector('input[type=file]');
        this.fileInput.addEventListener('change', this.changeFile.bind(this))
        this.preview = node.querySelector('.preview')
    }

    changeFile(event) {
        const files = event.target.files;
        if (files.length) {
            const file = files[0];
            // const para = document.createElement('p');
            // para.textContent

            this.preview.textContent = file.name;

        }

        console.log(files);
    }

}


const messageFiles = document.querySelectorAll('.message-file')
;[...messageFiles].forEach((node) => new MessageFile(node))
