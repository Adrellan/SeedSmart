export type CategoryKey =
  | 'arable'
  | 'rowCrops'
  | 'vegetables'
  | 'orchards'
  | 'forage'
  | 'industrial';

export const CATEGORY_OPTIONS: { key: CategoryKey; label: string }[] = [
  { key: 'arable',     label: 'Arable (cereals/oilseeds)' },
  { key: 'rowCrops',   label: 'Row crops' },
  { key: 'vegetables', label: 'Vegetables (fresh market/transplant)' },
  { key: 'orchards',   label: 'Orchards/Vineyards (perennial)' },
  { key: 'forage',     label: 'Forage crops (fodder/legumes)' },
  { key: 'industrial', label: 'Specialty industrial crops' },
];

export const TARGET_ZOOM = 10;
