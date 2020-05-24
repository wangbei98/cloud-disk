module.exports = {
    devServer:{
        host:'localhost',
        port:8080,
        proxy:{
            '/api':{
                target:'http://116.62.177.146',
                changeOrigin:true,
                logLevel: 'debug',
                pathRewrite:{
                    '/':'/api'
                }
            }
        }
    }
}
