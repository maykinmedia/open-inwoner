export class ReadOut {
  static selector = '.accessibility--read'

  constructor(node) {
    this.node = node

    this.speechSynthesis = window.speechSynthesis
    this.SpeechSynthesisUtterance = window.SpeechSynthesisUtterance
    this.isPaused = false // Track if speech is paused
    this.isReading = false // Track if speech is currently reading

    if ('speechSynthesis' in window) {
      this.node.addEventListener('click', this.handleReadPauseToggle)
    } else {
      this.node.parentElement.remove()
    }

    let voices = []
    const populateVoiceList = () => {
      voices = this.speechSynthesis.getVoices()
      // console.log(voices)
    }

    populateVoiceList()
    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = populateVoiceList
    }

    window.addEventListener('beforeunload', this.stopSpeech)
  }

  stopSpeech = () => {
    if (this.speechSynthesis.speaking || this.isPaused) {
      this.speechSynthesis.cancel()
      this.isPaused = false
      this.isReading = false
      this.updateButtonTextAndIcon(false)
    }
  }

  handleReadPauseToggle = (event) => {
    event.preventDefault()

    if (this.speechSynthesis.speaking && !this.isPaused) {
      // Pausing only when playing
      this.speechSynthesis.pause()
      this.isPaused = true
      this.updateButtonTextAndIcon(false)
    } else if (this.isPaused) {
      // Resume when paused
      this.speechSynthesis.resume()
      this.isPaused = false
      this.updateButtonTextAndIcon(true)
    } else {
      // When speech is not playing, start it
      let main = document.querySelector('.grid__main')
      if (!main) {
        main = document.querySelector('main')
      }

      // console.log(main.textContent)
      let text = this.getText(main)
      // console.log(text)
      const utterThis = new this.SpeechSynthesisUtterance(text)

      utterThis.onend = () => {
        this.isReading = false
        this.updateButtonTextAndIcon(false)
      }

      this.speechSynthesis.speak(utterThis)
      this.isReading = true
      this.isPaused = false
      this.updateButtonTextAndIcon(true) // Switch when speech starts
    }
  }

  updateButtonTextAndIcon(isReading) {
    const linkText = this.node.querySelector('.link__text')
    const icon = this.node.querySelector('.material-icons')

    linkText.textContent = isReading
      ? this.node.dataset.altText
      : this.node.dataset.text

    icon.textContent = isReading
      ? this.node.dataset.altIcon
      : this.node.dataset.icon

    this.node.setAttribute(
      'aria-label',
      isReading ? this.node.dataset.altText : this.node.dataset.text
    )
    this.node.setAttribute(
      'title',
      isReading ? this.node.dataset.altText : this.node.dataset.text
    )
  }

  getText = (node) => {
    let baseText = ''
    if (node.getAttribute('aria-hidden')) {
      return undefined
    }
    // console.log('node', node)
    if (node.childNodes) {
      for (let index = 0; index < node.childNodes.length; index++) {
        const childNode = node.childNodes[index]
        // console.log('childNode', childNode, baseText)
        if (childNode.nodeName === '#text') {
          if (childNode.nodeValue) {
            let nodeValue = childNode.nodeValue.replaceAll('\n', '').trim()
            if (
              nodeValue.replace(/\s/g, '') !== '' &&
              nodeValue.replace(/\s/g, '')
            ) {
              baseText += ` ${nodeValue}`
            }
          }
        } else {
          // console.log('test', childNode)
          const childText = this.getText(childNode)
          if (childText) {
            baseText += childText

            if (!baseText.endsWith('\n')) {
              baseText += '\n'
            }
          }
        }
      }
    }
    return baseText
  }
}

/**
 * Controls reading of content
 */
document
  .querySelectorAll(ReadOut.selector)
  .forEach((readOutButton) => new ReadOut(readOutButton))
