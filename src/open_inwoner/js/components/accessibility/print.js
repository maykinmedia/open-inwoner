const printButtons = document.querySelectorAll(".accessibility--print")

class Print {
    constructor(node) {
        this.node = node;
        this.node.addEventListener('click', this.print)
    }

    print(event) {
        event.preventDefault();
        window.print();
    }
}

[...printButtons].forEach((printButton) => new Print(printButton))
