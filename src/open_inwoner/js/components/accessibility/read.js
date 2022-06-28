const readOutButtons = document.querySelectorAll('.accessibility--read')

class ReadOut {
  constructor(node) {
    this.node = node

    this.speechSynthesis = window.speechSynthesis
    this.SpeechSynthesisUtterance = window.SpeechSynthesisUtterance
    if ('speechSynthesis' in window) {
      this.node.addEventListener('click', this.read)
    } else {
      this.node.parentElement.remove()
    }
  }

  read = (event) => {
    event.preventDefault()

    if (this.speechSynthesis.speaking) {
      this.speechSynthesis.pause()
    } else if (this.speechSynthesis.paused) {
      this.speechSynthesis.resume()
    } else {
      const main =
        typeof document === 'undefined' ? null : document.querySelector('main')

      var msg = new SpeechSynthesisUtterance()
      msg.text = main.textContent
      this.speechSynthesis.speak(msg)
    }
  }
}

;[...readOutButtons].forEach((readOutButton) => new ReadOut(readOutButton))
