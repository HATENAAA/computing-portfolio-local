const { defineConfig } = require('@vue/cli-service')
const path = require('path')
module.exports = defineConfig({
  publicPath: './',
  transpileDependencies: true,
  productionSourceMap: false,
  chainWebpack: config => {
    config.plugin('copy').tap(([options]) => {
      options.patterns.push({ from: path.resolve(__dirname, '../assets/atlas'), to: 'atlas' })
      return [options]
    })
  }
})
