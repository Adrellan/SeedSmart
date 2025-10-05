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

export const CROP_GROUP_COLORS: Record<CategoryKey, string> = {
  arable: '#ef4444',
  rowCrops: '#8b5cf6',
  vegetables: '#22c55e',
  orchards: '#f97316',
  forage: '#0ea5e9',
  industrial: '#facc15',
};

export const DEFAULT_CROP_COLOR = '#334155';

export const TARGET_ZOOM = 10;
