const path = require('path');
const webpack = require('webpack');
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");

module.exports = {
    mode: "production",
    entry: {
        index: './src/nutrition_tracker/assets/scripts/index.js',
        chart: './src/nutrition_tracker/assets/scripts/chart_util.js',
        style: './src/nutrition_tracker/assets/style/style.scss'
        },
    output: {
        filename: '[name].bundle.js',
        path: path.resolve(__dirname, './src/nutrition_tracker/static'),
    },
    module : {
        rules : [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: [],
            },
            {
                test: /\.s[ac]ss$/,
                exclude: /node_modules/,
                type: "asset/resource",
                generator: {
                    filename: "bundle.css"
                },
                use: ["sass-loader"],
            },
            {
                test: require.resolve("jquery"),
                loader: "expose-loader",
                options: {
                  exposes: ["$", "jQuery"],
                },
            },
        ],
    },
    optimization: {
        minimizer: [
        '...',
        new CssMinimizerPlugin()
        ]
    },
};
