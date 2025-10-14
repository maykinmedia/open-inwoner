const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const argv = require('yargs').argv

const paths = require('./build/paths')

// Set isProduction based on environment or argv.

let isProduction = process.env.NODE_ENV === 'production'
if (argv.production) {
  isProduction = true
}

/**
 * Webpack configuration
 * Run using "webpack" or "npm run build"
 */
module.exports = {
  // Entry points locations.
  entry: {
    [`${paths.package.name}-css`]: `${__dirname}/${paths.scssEntry}`,
    [`${paths.package.name}-js`]: `${__dirname}/${paths.jsEntry}`,

    admin_overrides: `${__dirname}/${paths.scssSrcDir}/admin/admin_overrides.scss`,
    'pdf-p': `${__dirname}/${paths.scssSrcDir}/pdf/pdf_portrait.scss`,
    'django-admin': `${__dirname}/${paths.jsSrcDir}/django-admin.js`,
  },

  // (Output) bundle locations.
  output: {
    path: __dirname + '/' + paths.jsDir,
    filename: '[name].js', // file
    chunkFilename: '[name].bundle.js',
    publicPath: '/static/bundles/',
  },

  // Plugins
  plugins: [new MiniCssExtractPlugin()],

  resolve: {
    alias: {
      'htmx.org': require.resolve('htmx.org'),
    },
  },

  // Modules
  module: {
    rules: [
      // .js
      {
        test: /src\/.*.js?$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
          },
        },
      },

      // .scss
      {
        test: /src\/.*.(sa|sc|c)ss$/,
        use: [
          // Writes css files.
          MiniCssExtractPlugin.loader,

          // Loads CSS files.
          {
            loader: 'css-loader',
            options: {
              url: false,
            },
          },

          // Runs postcss configuration (postcss.config.js).
          {
            loader: 'postcss-loader',
          },

          // Compiles .scss to .css.
          {
            loader: 'sass-loader',
            options: {
              sassOptions: {
                comments: false,
                style: 'compressed',
              },
              sourceMap: argv.sourcemap,
            },
          },
        ],
      },
    ],
  },

  // Use --production to optimize output.
  mode: isProduction ? 'production' : 'development',

  // Use --sourcemap to generate sourcemap.
  devtool: argv.sourcemap ? 'sourcemap' : false,
}
