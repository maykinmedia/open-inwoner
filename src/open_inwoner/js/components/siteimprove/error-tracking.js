/**
 * Note: users can upload multiple faulty files with their respective errors, and can delete them one by one,
 * Tracking should only happen on newly added errors, not the entire occurring set.
 */

// Mock _sz object for testing
if (typeof _sz === 'undefined') {
  var _sz = {
    push: function (data) {
      try {
        console.log('Event pushed to _sz:', data)
      } catch (error) {
        console.error('Error occurred while pushing event data:', error)
      }
    },
  }
}

let fileErrorObserver
let trackingEnabled = false
let lastErrorState = new Map()
let userHasSelectedFiles = false // Track only after user SELECTS a file
let previousErrorState = new Map() // Keeps track of errors before file selection

// Function to generate a unique identifier for each error element
function getErrorIdentifier(element) {
  return `${element.className}-${Array.from(
    element.parentNode.children
  ).indexOf(element)}`
}

// Detect and push only new errors that come into the DOM
function trackFileErrors() {
  if (!userHasSelectedFiles) {
    return
  }
  console.log('[trackFileErrors] Checking for file errors...')

  const errorElements = [
    ...document.querySelectorAll(
      '.file-error__size, .file-error__type, .file-error__type-size'
    ),
  ]
  const currentErrors = new Map()

  errorElements.forEach((element) => {
    const errorText = element.textContent.trim() || 'Unknown error'
    const errorId = getErrorIdentifier(element)
    currentErrors.set(errorId, errorText)
  })

  currentErrors.forEach((message, id) => {
    if (!previousErrorState.has(id)) {
      _sz.push(['event', 'Mijn Aanvragen', 'Error', message])
    }
  })

  // Update previous error state only with persistent errors
  previousErrorState = new Map(currentErrors)
}

// Start observing errors inside the file list
function startTracking() {
  if (trackingEnabled) {
    return
  }
  trackingEnabled = true

  const fileList = document.querySelector('#document-upload .file-list__list')
  if (!fileList) {
    return
  }

  fileErrorObserver = new MutationObserver(trackFileErrors)
  fileErrorObserver.observe(fileList, {
    childList: true,
    subtree: true,
    attributes: true,
  })
}

// Stop tracking errors
function stopTracking() {
  if (!trackingEnabled) {
    return
  }
  trackingEnabled = false

  if (fileErrorObserver) {
    fileErrorObserver.disconnect()
  }
}

// Check for form presence and start tracking
function checkAndStartTracking() {
  const documentUpload = document.getElementById('document-upload')

  if (documentUpload) {
    startTracking()
  } else {
    stopTracking()
  }
}

// Detect file selection
document.body.addEventListener('change', (event) => {
  const fileInput = document.querySelector(
    '#document-upload .file-input__input'
  )
  if (fileInput && event.target === fileInput) {
    userHasSelectedFiles = true
    console.log(
      '[change] User selected new files. Storing existing errors before tracking new ones.'
    )
    previousErrorState = new Map(lastErrorState)
    trackFileErrors()
  }
})

// Prevent duplicate tracking after clicks on delete buttons
document.body.addEventListener('click', (event) => {
  const deleteButton = event.target.closest('.file__delete')
  if (deleteButton) {
    return
  }
})

// HTMX event listener to restart tracking when content updates
document.body.addEventListener('htmx:afterSwap', () => {
  checkAndStartTracking()
})

// Initial setup
checkAndStartTracking()

// Dynamic observer
const formObserver = new MutationObserver(checkAndStartTracking)
formObserver.observe(document.body, { childList: true, subtree: true })
console.log('[Script] Created MutationObserver for form changes.')
