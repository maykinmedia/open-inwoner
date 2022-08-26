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

    let voices = []
    function populateVoiceList() {
      voices = this.speechSynthesis.getVoices()
      // console.log(voices)
    }

    populateVoiceList()
    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = populateVoiceList
    }
  }

  read = (event) => {
    event.preventDefault()

    if (this.speechSynthesis.speaking) {
      this.speechSynthesis.pause()
    } else if (this.speechSynthesis.paused) {
      this.speechSynthesis.resume()
    } else {
      let main = document.querySelector('.grid__main')
      if (!main) {
        main = document.querySelector('main')
      }

      // console.log(main.innerText)
      // console.log(main.textContent)
      let text = this.getText(main)
      // console.log(text)

      const utterThis = new SpeechSynthesisUtterance(text)
      this.speechSynthesis.speak(utterThis)
    }
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

;[...readOutButtons].forEach((readOutButton) => new ReadOut(readOutButton))
