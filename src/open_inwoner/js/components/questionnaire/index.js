const question = document.getElementById('question')
const stepIndicator = document.querySelector(
  '.step-indicator__list-item--active'
)

if (stepIndicator && question) {
  /*
   * Focus on the question only if it's the not the first one and if it's accessed via a mobile phone
   */
  if (window.innerWidth < 768 && stepIndicator.dataset.step > 1) {
    question.scrollIntoView()
  }
}
