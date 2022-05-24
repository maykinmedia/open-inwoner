const question = document.getElementById('question')
const stepIndicators = document.querySelectorAll(
  '.step-indicator__list-item--active'
)

stepIndicators.forEach((stepIndicator) => {
  if (window.innerWidth < 768 && stepIndicator.dataset.step > 1) {
    question.scrollIntoView()
  }
})
