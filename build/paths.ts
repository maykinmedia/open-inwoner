import pkg from '../package.json';

/** Src dir */
const sourcesRoot = `src/${pkg.name}/`;

/** "Main" static dir */
const staticRoot = `${sourcesRoot}static/`;

/**
 * Application path configuration for use in frontend scripts
 */
const paths = {
  // Parsed package.json
  package: pkg,

  // Path to the scss entry point
  scssEntry: `${sourcesRoot}scss/screen.scss`,

  // Path to the js entry point (source)
  jsEntry: `${sourcesRoot}js/index.js`,

  // Path to the frontend entry point (source)
  frontendEntry: `${sourcesRoot}react/main.ts`,

  // Secondary entry points
  adminOverridesEntry: `${sourcesRoot}scss/admin/admin_overrides.scss`,
  pdfPortraitEntry: `${sourcesRoot}scss/pdf/pdf_portrait.scss`,
  djangoAdminEntry: `${sourcesRoot}js/django-admin.js`,

  // Path to the (transpiled) js directory
  jsDir: `${staticRoot}bundles/`,
} as const;

export default paths;
