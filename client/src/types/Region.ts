export type RegionGeometry =
  | {
      type: 'Polygon';
      coordinates: number[][][];
    }
  | {
      type: 'MultiPolygon';
      coordinates: number[][][][];
    };

export interface RegionShape {
  name_latn: string;
  geom: RegionGeometry | null;
}
