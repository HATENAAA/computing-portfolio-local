const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  // Keep the original mobile proportions inside the desktop preview.
  css: { loaderOptions: { postcss: { postcssOptions: { plugins: [{
    postcssPlugin: 'medical-viewport',
    Declaration(decl) {
      if (decl.value.includes('vw') && !decl.value.includes('var(--medical-vw)')) {
        decl.value = decl.value.replace(/(-?\d*\.?\d+)vw\b/g, 'calc($1 * var(--medical-vw))')
      }
    }
  }] } } } },
  devServer:{
    port:8086
  },
  chainWebpack: config =>{
    config.plugin('html')
      .tap(args => {
        args[0].title = "体检APP预约";
        return args;
      })
  }
})
