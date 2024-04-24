const path = require('path');
const webpack = require('webpack');

module.exports = {
    mode: "production",
    entry: {
        index: './src/food_hub/assets/scripts/index.js',
        chart: './src/food_hub/assets/scripts/chart_util.js',
        style: './src/food_hub/assets/style/style.scss'
        },
    output: {
        filename: '[name].bundle.js',
        path: path.resolve(__dirname, './src/food_hub/static'),
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
};
