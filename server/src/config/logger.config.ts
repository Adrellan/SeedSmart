import winston from 'winston'
import winstonGelf from 'winston-gelf'

export const logger = winston.createLogger({
  transports: [
    new winston.transports.Console(),
    new winstonGelf({
      // You will find all gelfPro options here: https://www.npmjs.com/package/gelf-pro
      gelfPro: {
        fields: {
          env: process.env.NODE_ENV || 'development',
          pid: process.pid,
        },
        adapterName: 'udp',
        adapterOptions: {
          host: process.env.GRAYLOG_HOST || '127.0.0.1',
          port: 12201,
        }
      }
    })
  ]
});
