const enlargeButtons = document.querySelectorAll(".accessibility--enlarge-font")

class EnlageFont {
    constructor(node) {
        this.node = node;
        this.text = node.querySelector(".link__text");
        this.icon = node.querySelector(".material-icons");
        this.node.addEventListener('click', this.enlarge.bind(this))
    }

    enlarge(event) {
        event.preventDefault();
        let root = document.documentElement;
        const varName = '--font-size-body';
        const baseSize = '16px'
        const enlargeSize = "20px"

        if (root.style.getPropertyValue(varName) == enlargeSize) {
            root.style.setProperty(varName, baseSize);
            this.text.innerText = this.node.dataset.text;
            this.icon.innerText = this.node.dataset.icon;
        } else {
            root.style.setProperty(varName, enlargeSize);
            this.text.innerText = this.node.dataset.altText;
            this.icon.innerText = this.node.dataset.altIcon;
        }
    }
}

[...enlargeButtons].forEach((enlargeButton) => new EnlageFont(enlargeButton))
