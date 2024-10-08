// Get the end date from the Django context
const einddatum = new Date('{{ bericht.einddatum_handelingstermijn }}')
const today = new Date()

// Calculate the remaining days
const remainingTime = einddatum - today // in milliseconds
const remainingDays = Math.ceil(remainingTime / (1000 * 60 * 60 * 24)) // convert to days

// Display the result
const remainingDaysElement = document.getElementById('remainingDays')
if (remainingDaysElement) {
  console.log('ELEMNT {{ bericht.publicatiedatum }} BESTAAT')
  if (remainingDays > 0) {
    remainingDaysElement.textContent = `Er zijn nog ${remainingDays} dagen tot de einddatum.`
  } else if (remainingDays === 0) {
    remainingDaysElement.textContent = 'Vandaag is de einddatum.'
  } else {
    remainingDaysElement.textContent = 'De einddatum is verstreken.'
  }
}
