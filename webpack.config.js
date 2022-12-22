const path = require('path');
const BundleAnalyzerPlugin = require("webpack-bundle-analyzer").BundleAnalyzerPlugin

module.exports = {
    mode: "production",
    entry: './src/food_hub/assets/index.js',
    output: {
        filename: 'bundle.js',
        path: path.resolve(__dirname, './src/food_hub/static'),
    },
    plugins: [new BundleAnalyzerPlugin()],
};
