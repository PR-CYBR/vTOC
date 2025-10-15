import { telemetryAPI } from './api';

const normaliseCollection = (payload) => {
  if (!payload) {
    return [];
  }

  if (Array.isArray(payload)) {
    return payload;
  }

  if (Array.isArray(payload.results)) {
    return payload.results;
  }

  if (Array.isArray(payload.items)) {
    return payload.items;
  }

  return [];
};

const groupBySource = (items = [], formatter = (item) => item) => {
  return items.reduce((groups, item) => {
    const source = item.source || 'Unknown Source';
    const formatted = formatter(item);

    if (!formatted) {
      return groups;
    }

    if (!groups[source]) {
      groups[source] = [];
    }

    groups[source].push(formatted);
    return groups;
  }, {});
};

const toAssetMarker = (asset) => {
  if (
    typeof asset.latitude !== 'number' ||
    typeof asset.longitude !== 'number'
  ) {
    return null;
  }

  return {
    id: asset.id,
    name: asset.name || asset.callsign || 'Asset',
    latitude: asset.latitude,
    longitude: asset.longitude,
    heading: asset.heading ?? asset.bearing ?? null,
    speed: asset.speed ?? null,
    status: asset.status ?? asset.mode ?? null,
    timestamp: asset.timestamp ?? asset.last_update ?? null,
    source: asset.source,
  };
};

const toTrackPolyline = (track) => {
  const points = normaliseCollection(track.points || track.path || track.coordinates).map((point) => ({
    latitude: point.latitude ?? point.lat ?? (Array.isArray(point) ? point[0] : null),
    longitude: point.longitude ?? point.lng ?? point.lon ?? (Array.isArray(point) ? point[1] : null),
  }));

  const validPoints = points.filter(
    (point) => typeof point.latitude === 'number' && typeof point.longitude === 'number',
  );

  if (validPoints.length === 0) {
    return null;
  }

  return {
    id: track.id,
    name: track.name || track.callsign || 'Track',
    description: track.description || track.summary || null,
    color: track.color || track.stroke,
    points: validPoints,
    source: track.source,
  };
};

export const fetchTelemetryLayers = async () => {
  const [assetResponse, trackResponse] = await Promise.all([
    telemetryAPI.getAssetLocations(),
    telemetryAPI.getTracks(),
  ]);

  const assets = normaliseCollection(assetResponse.data).map(toAssetMarker).filter(Boolean);
  const tracks = normaliseCollection(trackResponse.data).map(toTrackPolyline).filter(Boolean);

  const assetLayers = groupBySource(assets, (asset) => asset);
  const trackLayers = groupBySource(tracks, (track) => track);

  const firstAsset = assets[0];
  const defaultCenter = firstAsset
    ? [firstAsset.latitude, firstAsset.longitude]
    : undefined;

  return {
    assetLayers,
    trackLayers,
    center: defaultCenter,
  };
};

export default fetchTelemetryLayers;
