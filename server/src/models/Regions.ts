import * as Sequelize from 'sequelize';
import { DataTypes, Model, Optional } from 'sequelize';

export interface RegionsAttributes {
  id: number;
  nuts_id: string;
  levl_code: number;
  cntr_code: string;
  name_latn: string;
  nuts_name: string;
  mount_type?: number;
  urbn_type?: number;
  coast_type?: number;
  geom?: any;
}

export type RegionsPk = "id";
export type RegionsId = Regions[RegionsPk];
export type RegionsOptionalAttributes = "id" | "mount_type" | "urbn_type" | "coast_type" | "geom";
export type RegionsCreationAttributes = Optional<RegionsAttributes, RegionsOptionalAttributes>;

export class Regions extends Model<RegionsAttributes, RegionsCreationAttributes> implements RegionsAttributes {
  id!: number;
  nuts_id!: string;
  levl_code!: number;
  cntr_code!: string;
  name_latn!: string;
  nuts_name!: string;
  mount_type?: number;
  urbn_type?: number;
  coast_type?: number;
  geom?: any;


  static initModel(sequelize: Sequelize.Sequelize): typeof Regions {
    return Regions.init({
    id: {
      autoIncrement: true,
      type: DataTypes.BIGINT,
      allowNull: false,
      primaryKey: true
    },
    nuts_id: {
      type: DataTypes.TEXT,
      allowNull: false
    },
    levl_code: {
      type: DataTypes.SMALLINT,
      allowNull: false
    },
    cntr_code: {
      type: DataTypes.TEXT,
      allowNull: false
    },
    name_latn: {
      type: DataTypes.TEXT,
      allowNull: false
    },
    nuts_name: {
      type: DataTypes.TEXT,
      allowNull: false
    },
    mount_type: {
      type: DataTypes.SMALLINT,
      allowNull: true
    },
    urbn_type: {
      type: DataTypes.SMALLINT,
      allowNull: true
    },
    coast_type: {
      type: DataTypes.SMALLINT,
      allowNull: true
    },
    geom: {
      type: DataTypes.GEOMETRY('MULTIPOLYGON', 4326),
      allowNull: true
    }
  }, {
    sequelize,
    tableName: 'Regions',
    schema: 'public',
    timestamps: false,
    indexes: [
      {
        name: "nuts60_geom_gix",
        fields: [
          { name: "geom" },
        ]
      },
      {
        name: "nuts60_nuts_id_uidx",
        unique: true,
        fields: [
          { name: "nuts_id" },
        ]
      },
      {
        name: "nuts60_pkey",
        unique: true,
        fields: [
          { name: "id" },
        ]
      },
    ]
  });
  }
}
