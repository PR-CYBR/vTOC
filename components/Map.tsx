'use client';

import { useEffect, useRef, useState } from 'react';
import type { Map as LeafletMap, TileLayer as LeafletTileLayer } from 'leaflet';

type BaseMapType = 'streets' | 'satellite';
type OverlayType = 'sensor-ranges' | 'heatmap';

interface GeoJSONFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: number[] | number[][] | number[][][];
  };
  properties?: Record<string, unknown>;
}

interface GeoJSONData {
  type: string;
  features: GeoJSONFeature[];
}

export default function Map() {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<LeafletMap | null>(null);
  const tileLayerRef = useRef<LeafletTileLayer | null>(null);
  const geoJsonLayerRef = useRef<any>(null);
  
  const [baseMap, setBaseMap] = useState<BaseMapType>('streets');
  const [overlays, setOverlays] = useState<Set<OverlayType>>(new Set());
  const [geoJsonUrl, setGeoJsonUrl] = useState('');
  const [geoJsonData, setGeoJsonData] = useState<GeoJSONData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize map
  useEffect(() => {
    if (!mapRef.current) return;
    
    // Check if map is already initialized
    if (mapInstanceRef.current) {
      return;
    }

    // Dynamic import to avoid SSR issues
    import('leaflet').then((L) => {
      // Ensure the container is not already initialized
      if (mapInstanceRef.current) return;
      
      // Fix Leaflet default icon paths
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      });

      const map = L.map(mapRef.current!, {
        center: [39.8283, -98.5795], // Center of USA
        zoom: 4,
        zoomControl: true,
      });

      mapInstanceRef.current = map;

      // Add dark tile layer
      const darkTileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
      const attribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
      
      tileLayerRef.current = L.tileLayer(darkTileUrl, {
        attribution,
        maxZoom: 19,
      }).addTo(map);
    });

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Handle base map changes
  useEffect(() => {
    if (!mapInstanceRef.current || !tileLayerRef.current) return;

    import('leaflet').then((L) => {
      tileLayerRef.current?.remove();

      let tileUrl: string;
      let attribution: string;

      if (baseMap === 'streets') {
        tileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
        attribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
      } else {
        tileUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
        attribution = 'Tiles &copy; Esri';
      }

      tileLayerRef.current = L.tileLayer(tileUrl, {
        attribution,
        maxZoom: 19,
      }).addTo(mapInstanceRef.current!);
    });
  }, [baseMap]);

  // Handle GeoJSON loading
  const handleLoadGeoJson = async () => {
    if (!geoJsonUrl.trim()) {
      setError('Please enter a valid URL');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(geoJsonUrl);
      if (!response.ok) throw new Error('Failed to fetch GeoJSON');
      
      const data = await response.json();
      setGeoJsonData(data);
      
      // Add to map
      if (mapInstanceRef.current) {
        import('leaflet').then((L) => {
          // Remove existing layer
          if (geoJsonLayerRef.current) {
            geoJsonLayerRef.current.remove();
          }

          // Add new GeoJSON layer
          geoJsonLayerRef.current = L.geoJSON(data, {
            style: () => ({
              color: '#38bdf8',
              weight: 2,
              opacity: 0.8,
              fillOpacity: 0.4,
            }),
            onEachFeature: (feature, layer) => {
              if (feature.properties) {
                const props = Object.entries(feature.properties)
                  .map(([k, v]) => `<strong>${k}:</strong> ${v}`)
                  .join('<br>');
                layer.bindPopup(props);
              }
            },
          }).addTo(mapInstanceRef.current!);

          // Fit bounds to GeoJSON
          const bounds = geoJsonLayerRef.current.getBounds();
          if (bounds.isValid()) {
            mapInstanceRef.current!.fitBounds(bounds, { padding: [50, 50] });
          }
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load GeoJSON');
    } finally {
      setLoading(false);
    }
  };

  const toggleOverlay = (overlay: OverlayType) => {
    setOverlays((prev) => {
      const next = new Set(prev);
      if (next.has(overlay)) {
        next.delete(overlay);
      } else {
        next.add(overlay);
      }
      return next;
    });
  };

  return (
    <div className="map-container">
      {/* Map controls overlay */}
      <div className="map-controls">
        {/* Base map switcher */}
        <div className="map-control-group">
          <div className="map-control-label">Base Map</div>
          <div className="map-control-buttons">
            <button
              className={`map-control-btn ${baseMap === 'streets' ? 'map-control-btn--active' : ''}`}
              onClick={() => setBaseMap('streets')}
            >
              Streets
            </button>
            <button
              className={`map-control-btn ${baseMap === 'satellite' ? 'map-control-btn--active' : ''}`}
              onClick={() => setBaseMap('satellite')}
            >
              Satellite
            </button>
          </div>
        </div>

        {/* Overlay toggles */}
        <div className="map-control-group">
          <div className="map-control-label">Overlays</div>
          <div className="map-control-buttons">
            <button
              className={`map-control-btn ${overlays.has('sensor-ranges') ? 'map-control-btn--active' : ''}`}
              onClick={() => toggleOverlay('sensor-ranges')}
            >
              📡 Sensors
            </button>
            <button
              className={`map-control-btn ${overlays.has('heatmap') ? 'map-control-btn--active' : ''}`}
              onClick={() => toggleOverlay('heatmap')}
            >
              🔥 Heatmap
            </button>
          </div>
        </div>

        {/* GeoJSON input */}
        <div className="map-control-group map-geojson-input">
          <div className="map-control-label">Import GeoJSON</div>
          <input
            type="text"
            placeholder="Enter GeoJSON URL..."
            value={geoJsonUrl}
            onChange={(e) => setGeoJsonUrl(e.target.value)}
            className="map-input"
            onKeyDown={(e) => e.key === 'Enter' && handleLoadGeoJson()}
          />
          <button
            className="map-control-btn map-control-btn--primary"
            onClick={handleLoadGeoJson}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Load'}
          </button>
          {error && <div className="map-error">{error}</div>}
          {geoJsonData && !error && (
            <div className="map-success">
              ✓ Loaded {geoJsonData.features?.length || 0} features
            </div>
          )}
        </div>
      </div>

      {/* Map container */}
      <div ref={mapRef} className="map-view" />
    </div>
  );
}
