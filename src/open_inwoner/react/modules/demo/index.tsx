import { Root } from 'react-dom/client';
import Demo from './Demo';
import { AbstractPage } from '@react/lib/abstractPage';

export default class Page extends AbstractPage {
  static reactRoot: Root;

  static get rootNode() {
    return document.querySelector('#react-root-demo')!;
  }

  static get countNode(): HTMLDivElement | null {
    return document.querySelector('#react-root-demo-count');
  }
  static get counterNode(): HTMLDivElement | null {
    return document.querySelector('#react-root-demo-counter');
  }

  static get root() {
    return <Demo countNode={this.countNode} counterNode={this.counterNode} />;
  }
}
