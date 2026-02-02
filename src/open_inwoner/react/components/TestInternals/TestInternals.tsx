// import { Component, ComponentChildren, RenderableProps } from 'preact';
// import register from 'preact-custom-element';

// class Greeting extends Component<{ name: string }> {
//   // internals_: any;
//   // constructor() {
//   // super();
//   //     this.internals_ = this.attachInternals();
//   // }

//     // Register as <x-greeting>:

//     constructor() {
//         super()

//         this.internals_ = new HTMLElement().attachInternals();
//     }
//   static tagName = 'x-greeting';

//   // Track these attributes:
//   static observedAttributes = ['name'];
//   // static internals =
//   render(
//     props?: RenderableProps<{ name: string }, any> | undefined,
//     state?: Readonly<{}> | undefined,
//     context?: any
//   ): ComponentChildren {
//     return <p>{props?.name}</p>;
//   }
//   //   render() {
//   //     return <p>Hello, {this.props.name}!</p>;
// }

// Greeting.tagName = 'test-x';

// register(Greeting);
const defa = () => {
  class CustomCheckbox extends HTMLElement {
    static formAssociated = true;
    internals_;

    constructor() {
      super();
      this.internals_ = this.attachInternals();
      this.internals_.role = 'test';
    }

    // …
  }

  window.customElements.define('custom-checkbox', CustomCheckbox);

  let element = document.createElement('custom-checkbox') as CustomCheckbox;
  let form = document.createElement('form');

  // Append element to form to associate it
  form.appendChild(element);

  console.log(element.internals_.form, element.internals_.role);
  return element;
};

export default defa;
