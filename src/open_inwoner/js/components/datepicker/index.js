import flatpickr from 'flatpickr'
import { Dutch } from 'flatpickr/dist/l10n/nl'

const instance = flatpickr('.datefield', {
  weekNumbers: true,
  dateFormat: 'd-m-Y',
  locale: Dutch,
  onReady: function (dateObj, dateStr, instance) {
    let cal = instance.calendarContainer
    if (cal.querySelectorAll('.flatpickr-clear').length < 1) {
      let clear = document.createElement('div')
      clear.innerText = 'Verwijder'
      clear.classList.add('flatpickr-clear')
      cal.append(clear)
      cal.querySelector('.flatpickr-clear').addEventListener('click', () => {
        instance.clear()
        instance.close()
      })
    }
  },
})
