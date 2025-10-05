export interface SowingMapGeometry {
  type: string;
  coordinates: unknown;
}

export interface SowingMapFeature {
  geometry: SowingMapGeometry;
  crop_group?: string | null;
  properties?: Record<string, unknown>;
}

export interface SowingMapResponse {
  count: number;
  features: SowingMapFeature[];
}
