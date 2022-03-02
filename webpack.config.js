const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const argv = require('yargs').argv;
const { styles } = require( '@ckeditor/ckeditor5-dev-utils' );

const paths = require('./build/paths');

// Set isProduction based on environment or argv.

let isProduction = process.env.NODE_ENV === 'production';
if (argv.production) {
    isProduction = true;
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

        'admin_overrides': `${__dirname}/${paths.scssSrcDir}/admin/admin_overrides.scss`,
        'pdf-p': `${__dirname}/${paths.scssSrcDir}/pdf/pdf_portrait.scss`,
    },

    // (Output) bundle locations.
    output: {
        path: __dirname + '/' + paths.jsDir,
        filename: '[name].js', // file
        chunkFilename: '[name].bundle.js',
        publicPath: '/static/bundles/',
    },

    // Plugins
    plugins: [
        new MiniCssExtractPlugin(),
    ],

    // Modules
    module: {
        rules: [
            // CKEditor
            {
                test: /ckeditor5-[^/\\]+[/\\]theme[/\\]icons[/\\][^/\\]+\.svg$/,
                use: [ 'raw-loader' ]
            },
            {
                test: /ckeditor5-[^/\\]+[/\\]theme[/\\].+\.css$/,
                use: [
                    {
                        loader: 'style-loader',
                        options: {
                            injectType: 'singletonStyleTag',
                            attributes: {
                                'data-cke': true
                            }
                        }
                    },
                    {
                        loader: 'postcss-loader',
                        options: styles.getPostCssConfig( {
                            themeImporter: {
                                themePath: require.resolve( '@ckeditor/ckeditor5-theme-lark' )
                            },
                            minify: true
                        } )
                    }
                ]
            },

            // .js
            {
                test: /src\/.*.js?$/,
                exclude: /node_modules/,
                loader: 'babel-loader',
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
                            url: false
                        },
                    },

                    // Runs postcss configuration (postcss.config.js).
                    {
                        loader: 'postcss-loader'
                    },

                    // Compiles .scss to .css.
                    {
                        loader: 'sass-loader',
                        options: {
                            sassOptions: {
                                comments: false,
                                style: 'compressed'
                            },
                            sourceMap: argv.sourcemap
                        },
                    },
                ],
            },
        ]
    },

    // Use --production to optimize output.
    mode: isProduction ? 'production' : 'development',

    // Use --sourcemap to generate sourcemap.
    devtool: argv.sourcemap ? 'sourcemap' : false,
};
