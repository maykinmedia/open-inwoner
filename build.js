import esbuild from 'esbuild'
import svg from 'esbuild-plugin-svg'
import sassPlugin from 'esbuild-plugin-sass'

esbuild
  .build({
    entryPoints: [
      'src/open_inwoner/js/index.js',
      // 'src/open_inwoner/scss/screen.scss',
    ],
    bundle: true,
    minify: true,
    sourcemap: true,
    outdir: './src/open_inwoner/static/bundles/',
    plugins: [sassPlugin(), svg()],
  })
  .catch((e) => console.error(e.message))
