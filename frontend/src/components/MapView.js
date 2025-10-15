import React, { useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  LayersControl,
  LayerGroup,
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const DEFAULT_CENTER = [38.8951, -77.0364];
const DEFAULT_ZOOM = 5;

function MapView({ assetLayers, trackLayers, center = DEFAULT_CENTER, zoom = DEFAULT_ZOOM }) {
  const hasTelemetry = useMemo(() => {
    const assetCount = Object.values(assetLayers || {}).reduce(
      (total, layerAssets) => total + layerAssets.length,
      0,
    );
    const trackCount = Object.values(trackLayers || {}).reduce(
      (total, layerTracks) => total + layerTracks.length,
      0,
    );
    return assetCount + trackCount > 0;
  }, [assetLayers, trackLayers]);

  return (
    <div className="map-view">
      <MapContainer center={center} zoom={zoom} minZoom={2} maxZoom={18} scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <LayersControl position="topright">
          {Object.entries(assetLayers || {}).map(([source, assets]) => (
            <LayersControl.Overlay
              key={`assets-${source}`}
              name={`Assets: ${source}`}
              checked
            >
              <LayerGroup>
                {assets.map((asset) => (
                  <Marker key={asset.id || `${source}-${asset.name}`} position={[asset.latitude, asset.longitude]}>
                    <Popup>
                      <div className="map-popup">
                        <strong>{asset.name || 'Asset'}</strong>
                        {asset.status ? <div>Status: {asset.status}</div> : null}
                        {asset.heading != null ? <div>Heading: {asset.heading}&deg;</div> : null}
                        {asset.speed != null ? <div>Speed: {asset.speed} kn</div> : null}
                        <div>
                          Lat/Lng: {asset.latitude.toFixed(4)}, {asset.longitude.toFixed(4)}
                        </div>
                        {asset.timestamp ? <div>Updated: {new Date(asset.timestamp).toLocaleString()}</div> : null}
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </LayerGroup>
            </LayersControl.Overlay>
          ))}

          {Object.entries(trackLayers || {}).map(([source, tracks]) => (
            <LayersControl.Overlay
              key={`tracks-${source}`}
              name={`Tracks: ${source}`}
              checked
            >
              <LayerGroup>
                {tracks.map((track) => (
                  <Polyline
                    key={track.id || `${source}-${track.name}`}
                    positions={track.points.map((point) => [point.latitude, point.longitude])}
                    pathOptions={{ color: track.color || '#007bff', weight: 3, opacity: 0.8 }}
                  >
                    <Popup>
                      <div className="map-popup">
                        <strong>{track.name || 'Track'}</strong>
                        {track.description ? <div>{track.description}</div> : null}
                        {track.points?.length ? (
                          <div>{track.points.length} points</div>
                        ) : null}
                      </div>
                    </Popup>
                  </Polyline>
                ))}
              </LayerGroup>
            </LayersControl.Overlay>
          ))}
        </LayersControl>

      </MapContainer>

      {!hasTelemetry && (
        <div className="map-empty-state">
          <div>No telemetry available yet. Connect a telemetry source to see live updates.</div>
        </div>
      )}
    </div>
  );
}

MapView.propTypes = {
  assetLayers: PropTypes.objectOf(
    PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
        name: PropTypes.string,
        latitude: PropTypes.number.isRequired,
        longitude: PropTypes.number.isRequired,
        heading: PropTypes.number,
        speed: PropTypes.number,
        status: PropTypes.string,
        timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      }),
    ),
  ),
  trackLayers: PropTypes.objectOf(
    PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
        name: PropTypes.string,
        description: PropTypes.string,
        color: PropTypes.string,
        points: PropTypes.arrayOf(
          PropTypes.shape({
            latitude: PropTypes.number.isRequired,
            longitude: PropTypes.number.isRequired,
          }),
        ),
      }),
    ),
  ),
  center: PropTypes.arrayOf(PropTypes.number),
  zoom: PropTypes.number,
};

MapView.defaultProps = {
  assetLayers: {},
  trackLayers: {},
  center: DEFAULT_CENTER,
  zoom: DEFAULT_ZOOM,
};

export default MapView;
