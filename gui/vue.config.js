module.exports = {
    runtimeCompiler: true,
    pluginOptions: {
        electronBuilder: {
          preload: 'src/preload.js',
          nodeIntegration: true
        }
      }
}