import type { Sequelize } from "sequelize";
import { Countires as _Countires } from "./Countires";
import type { CountiresAttributes, CountiresCreationAttributes } from "./Countires";
import { Regions as _Regions } from "./Regions";
import type { RegionsAttributes, RegionsCreationAttributes } from "./Regions";

export {
  _Countires as Countires,
  _Regions as Regions,
};

export type {
  CountiresAttributes,
  CountiresCreationAttributes,
  RegionsAttributes,
  RegionsCreationAttributes,
};

export function initModels(sequelize: Sequelize) {
  const Countires = _Countires.initModel(sequelize);
  const Regions = _Regions.initModel(sequelize);


  return {
    Countires: Countires,
    Regions: Regions,
  };
}
