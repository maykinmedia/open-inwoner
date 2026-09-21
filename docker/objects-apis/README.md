# Objects API / Objecttypes API

Backs the "Mijn taken" plugin's "externe taken"
(`TasksConfig.object_type_dimpact`).

Unlike Open Klant/Open Afval, these two images auto-`loaddata` every `*.json`
under `/app/fixtures/` on every start -- no `*-seed` service needed.

- `fixtures/objecttypes_api_fixtures.json` registers the object types, including
  "Extern Formulier Taak" (schema copied from
  `src/open_inwoner/cms/plugins/api_models/externe_formulier_taak.json`).
- `fixtures/objects_api_fixtures.json` holds the API tokens/permissions plus
  three demo "Extern Formulier Taak" objects for BSN `111222333` (the DigiD-mock
  `testuser`) -- log in locally and open the homepage to see them under "Mijn
  taken".
