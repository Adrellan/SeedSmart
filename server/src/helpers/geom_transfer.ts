import proj4 from 'proj4';

// 3857 -> 4326 transzformer
export const toWGS84 = proj4('EPSG:3857', 'EPSG:4326');

export type Position = [number, number] | [number, number, number];

// Koordináta(halmaz) transzformálása a geometry típusa szerint
export function transformCoords(type: string, coords: any): any {
  switch (type) {
    case 'Point':
      return transformPosition(coords as Position);
    case 'MultiPoint':
    case 'LineString':
      return (coords as Position[]).map(transformPosition);
    case 'MultiLineString':
    case 'Polygon':
      return (coords as Position[][]).map(ring => ring.map(transformPosition));
    case 'MultiPolygon':
      return (coords as Position[][][]).map(poly => poly.map(ring => ring.map(transformPosition)));
    case 'GeometryCollection':
      // GeometryCollection-ben a geometry-ket külön kezeljük – ezt a szintet a hívó rendezi.
      return coords;
    default:
      return coords;
  }
}

export function transformPosition(p: Position): Position {
  // [x,y] (3857) -> [lon,lat] (4326). Meghagyjuk az esetleges Z-t.
  const [x, y, z] = p as any;
  const [lon, lat] = toWGS84.forward([x, y]);
  return (z !== undefined) ? [lon, lat, z] as Position : [lon, lat] as Position;
}

export function transformGeometryTo4326(geom: any): any {
  if (!geom) return geom;
  if (geom.type === 'GeometryCollection' && Array.isArray(geom.geometries)) {
    return {
      type: 'GeometryCollection',
      geometries: geom.geometries.map(transformGeometryTo4326),
    };
  }
  return {
    ...geom,
    coordinates: transformCoords(geom.type, geom.coordinates),
  };
}
export function transformFeatureTo4326(feature: any): any {
  if (!feature || feature.type !== 'Feature') return feature;
  const out: any = { ...feature, geometry: transformGeometryTo4326(feature.geometry) };
  // bbox esetén is reprojectálunk (minX,minY,maxX,maxY) -> [minLon,minLat,maxLon,maxLat]
  if (Array.isArray(feature.bbox) && feature.bbox.length >= 4) {
    const [minX, minY, maxX, maxY] = feature.bbox;
    const [minLon, minLat] = toWGS84.forward([minX, minY]);
    const [maxLon, maxLat] = toWGS84.forward([maxX, maxY]);
    out.bbox = [minLon, minLat, maxLon, maxLat];
  }
  // GeoJSON-ben a CRS mezőt (ha lenne) érdemes elhagyni; implicit WGS84.
  if (out.crs) delete out.crs;
  return out;
}

export function transformFeatureCollectionTo4326(fc: any): any {
  if (!fc) return fc;
  if (fc.type === 'FeatureCollection' && Array.isArray(fc.features)) {
    const out: any = { ...fc, features: fc.features.map(transformFeatureTo4326) };
    if (Array.isArray(fc.bbox) && fc.bbox.length >= 4) {
      const [minX, minY, maxX, maxY] = fc.bbox;
      const [minLon, minLat] = toWGS84.forward([minX, minY]);
      const [maxLon, maxLat] = toWGS84.forward([maxX, maxY]);
      out.bbox = [minLon, minLat, maxLon, maxLat];
    }
    if (out.crs) delete out.crs;
    return out;
  }
  // Ha nem FeatureCollection, de Feature, akkor is próbáljuk konzisztensen:
  if (fc.type === 'Feature') return transformFeatureTo4326(fc);
  // Ha „sima” geometry jön vissza:
  if (fc.type && fc.coordinates) return transformGeometryTo4326(fc);
  return fc;
}