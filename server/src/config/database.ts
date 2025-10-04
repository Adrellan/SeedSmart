import { Sequelize } from 'sequelize';
import { initModels } from '../models/init-models';

const sequelize = new Sequelize(process.env.POSTGRES_URI!, {
  dialect: 'postgres',
  logging: false,
});

export const models = initModels(sequelize);
export { sequelize };