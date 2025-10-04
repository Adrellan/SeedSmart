import * as Sequelize from 'sequelize';
import { DataTypes, Model, Optional } from 'sequelize';

export interface CountiresAttributes {
  id: number;
  name: string;
  cntr_code?: string;
}

export type CountiresPk = "id";
export type CountiresId = Countires[CountiresPk];
export type CountiresOptionalAttributes = "cntr_code";
export type CountiresCreationAttributes = Optional<CountiresAttributes, CountiresOptionalAttributes>;

export class Countires extends Model<CountiresAttributes, CountiresCreationAttributes> implements CountiresAttributes {
  id!: number;
  name!: string;
  cntr_code?: string;


  static initModel(sequelize: Sequelize.Sequelize): typeof Countires {
    return Countires.init({
    id: {
      type: DataTypes.DECIMAL,
      allowNull: false,
      primaryKey: true
    },
    name: {
      type: DataTypes.TEXT,
      allowNull: false
    },
    cntr_code: {
      type: DataTypes.TEXT,
      allowNull: true
    }
  }, {
    sequelize,
    tableName: 'Countires',
    schema: 'public',
    timestamps: false,
    indexes: [
      {
        name: "Countires_pkey",
        unique: true,
        fields: [
          { name: "id" },
        ]
      },
    ]
  });
  }
}
