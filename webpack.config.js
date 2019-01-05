var path = require("path");
var webpack = require("webpack");
// var ExtractTextPlugin = require("extract-text-webpack-plugin");
var ExtractTextPlugin = require("mini-css-extract-plugin");

var nodePath = path.resolve(__dirname, "node_modules");
var distPath = path.resolve(__dirname, "static/dist");
var jsPath = path.resolve(__dirname, "static/javascripts");

module.exports = {
  stats: {
    entrypoints: false,
    children: false
  },

  entry: {
    index: path.join(jsPath, "main.jsx"),
    success: path.join(jsPath, "success.jsx")
  },

  output: {
    path: distPath,
    filename: "[name].js",
    sourceMapFilename: "[file].map",
    publicPath: distPath
  },

  resolve: {
    extensions: [".js", ".jsx", ".json", ".coffee", ".css", ".scss"]
  },

  module: {
    rules: [
      {
        test: /\.jsx$/,
        exclude: /node_modules/,
        loader: "babel-loader",
        query: {
          presets: [
            "@babel/preset-env",
            "@babel/preset-react",
            { plugins: ["@babel/plugin-proposal-class-properties"] }
          ]
        }
      },
      {
        test: /\.html$/,
        loader: "file?name=[name].[ext]"
      },
      {
        test: /\.(woff2|woff|ttf|eot)$/,
        loader: "file?name=fonts/[name].[ext]"
      },
      {
        test: /\.scss$/,
        use: [ExtractTextPlugin.loader, "css-loader", "sass-loader"]
        // loader: ExtractTextPlugin.extract(
        //   "css-loader?sourceMap!sass-loader?sourceMap=true&sourceMapContents=true"
        // )
      },
      {
        test: /\.(png|jpg|svg|ico)$/,
        loader: "file-loader?name=[path][name].[ext]"
      }
    ]
  },

  plugins: [new ExtractTextPlugin("[name].css")],

  devtool: "source-map"
};
