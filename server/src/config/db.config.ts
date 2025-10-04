import { sequelize } from './database';
import { logger } from './logger.config';

export const db = {
  init: async () => {
    try {
      await sequelize.authenticate();
      logger.info("✅  Database connected successfully!");
    } catch (error) {
      logger.error("❌  Unable to connect to the database:", error);
    }
  }
};