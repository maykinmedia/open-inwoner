import flatpickr from 'flatpickr'
import { Dutch } from 'flatpickr/dist/l10n/nl'

flatpickr('.datefield', {
  weekNumbers: true,
  dateFormat: 'd-m-Y',
  locale: Dutch,
})
