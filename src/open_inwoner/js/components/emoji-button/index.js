import { EmojiButton } from '@joeattardi/emoji-button';

/** @type {NodeList} All the emoji buttons. */
const EMOJI_BUTTONS = document.querySelectorAll('.emoji-button');


/**
 * Allows selecting emojis.
 */
class EmojiButtonSelector {
  /**
   * Constructor method.
   * @param {HTMLElement} node
   */
  constructor(node) {
    /** @type {HTMLElement} */
    this.node = node;

    /** @type {EmojiButton} */
    this.picker = this.getPicker();

    this.bindEvents();
  }

  /**
   * Binds events to callbacks.
   */
  bindEvents() {
    this.node.addEventListener('click', () => this.getPicker().togglePicker(this.node));
    this.getPicker().on('emoji', this.onEmoji.bind(this));
  }

  /**
   * Returns the input to add emoji's to.
   * @return {HTMLElement}
   */
  getInput() {
    return this.node.parentElement?.parentElement?.querySelector('input, textarea');
  }

  /**
   * Returns/instantiates the picker instances.
   * @return {EmojiButton}
   */
  getPicker() {
    if(!this.picker) {
      this.picker = new EmojiButton();
    }

    return this.picker;
  }

  /**
   * Gets called when an emoji is selected.
   * @param {Object} selection
   */
  onEmoji(selection) {
    const input = this.getInput();
    const emoji = selection.emoji;
    input.value += emoji;
  }
}

// Start1
[...EMOJI_BUTTONS].forEach((node) => new EmojiButtonSelector(node));
