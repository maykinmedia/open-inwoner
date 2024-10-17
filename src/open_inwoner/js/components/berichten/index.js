const berichtDataJsonElement = document.getElementById('bericht-data-json')

if (berichtDataJsonElement) {
  const berichtData = JSON.parse(berichtDataJsonElement.textContent)
  const einddatum = new Date(berichtData.einddatumHandelingstermijn)
  const today = new Date()

  // Calculate the remaining days
  const remainingTime = einddatum - today // in milliseconds
  const remainingDays = Math.ceil(remainingTime / (1000 * 60 * 60 * 24)) // convert to days

  // Display the result
  const remainingDaysElement = document.getElementById('remainingDays')
  if (remainingDaysElement) {
    if (remainingDays > 0) {
      remainingDaysElement.textContent = `Er zijn nog ${remainingDays} dagen tot de einddatum.`
    } else if (remainingDays === 0) {
      remainingDaysElement.textContent = 'Vandaag is de einddatum.'
    } else {
      remainingDaysElement.textContent = 'De einddatum is verstreken.'
    }
  } else console.error('Unable to find #remainingDays')
}
