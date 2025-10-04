const DotenvWebpackPlugin = require('dotenv-webpack');
const path = require('path');
const nodeExternals = require('webpack-node-externals');
const NodemonPlugin = require('nodemon-webpack-plugin'); // Ding

module.exports = env => { 
  console.log('env:', env);
  return {
  mode: 'development',
  entry: './src/index.ts',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
    clean: true,
  },
  target: 'node',
  optimization: {
    minimize: false,
  },
  externals: [
    nodeExternals(),
  ],
  plugins: [
    new NodemonPlugin(), // Dong
    new DotenvWebpackPlugin({
      path: './.env.' + Object.keys(env).slice(-1)[0],
    }),
  ],
  watch: false,
  module: {
    rules: [
      {
        test: /\.ts$/,
        exclude: /node_modules/,
        use: {
          loader: 'ts-loader',
          options: {
            transpileOnly: true, // Típusellenőrzés figyelmen kívül hagyása
          },
        },
      },
      {
        test: /\.(png|jpe?g|gif|svg)$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: '[name].[hash].[ext]',
              outputPath: 'images/',
            },
          },
        ],
      },
    ],
  },
  resolve: {
    extensions: ['.ts', '.js'],
  },
}};