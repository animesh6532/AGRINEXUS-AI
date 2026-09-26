import React, { useState, useEffect, useRef } from 'react';
import {
  MapPin,
  LocateFixed,
  Search,
  Plus,
  Minus,
  Navigation,
  Trash2,
  RefreshCw,
  Layers,
  Check,
  X,
  Maximize2,
  HelpCircle,
  Calculator,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Badge } from '../ui/Badge';

interface FieldMapEditorProps {
  initialFieldName?: string;
  initialAreaValue?: number;
  initialAreaUnit?: string;
  initialLat?: number;
  initialLng?: number;
  initialBoundary?: { type: 'Polygon'; coordinates: number[][][] } | null;
  farmId: number;
  onSave: (fieldData: any) => Promise<void>;
  onCancel: () => void;
}

export const FieldMapEditor: React.FC<FieldMapEditorProps> = ({
  initialFieldName = '',
  initialAreaValue = 1.0,
  initialAreaUnit = 'acre',
  initialLat = 22.5726,
  initialLng = 88.3639,
  initialBoundary = null,
  farmId,
  onSave,
  onCancel,
}) => {
  const [fieldName, setFieldName] = useState(initialFieldName || 'New Field');
  const [manualArea, setManualArea] = useState<number>(initialAreaValue);
  const [areaUnit, setAreaUnit] = useState<string>(initialAreaUnit);

  const [mapMode, setMapMode] = useState<'standard' | 'satellite'>('satellite');
  const [zoom, setZoom] = useState<number>(15);
  const [centerLat, setCenterLat] = useState<number>(initialLat);
  const [centerLng, setCenterLng] = useState<number>(initialLng);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);

  // Polygon Vertices: Array of [lat, lng]
  const [vertices, setVertices] = useState<[number, number][]>(() => {
    if (initialBoundary && initialBoundary.coordinates && initialBoundary.coordinates[0]) {
      return initialBoundary.coordinates[0].map(([lng, lat]) => [lat, lng]);
    }
    return [];
  });

  const [activeVertexIdx, setActiveVertexIdx] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const mapRef = useRef<HTMLDivElement>(null);

  // Geodesic Area Calculation (Spherical Gauss-Bonnet formula in m²)
  const calculateGeodesicAreaM2 = (pts: [number, number][]): number => {
    if (pts.length < 3) return 0;
    const R = 6378137.0; // Earth radius in meters
    let total = 0;
    const ring = [...pts];
    if (ring[0][0] !== ring[ring.length - 1][0] || ring[0][1] !== ring[ring.length - 1][1]) {
      ring.push(ring[0]);
    }
    for (let i = 0; i < ring.length - 1; i++) {
      const p1 = ring[i];
      const p2 = ring[i + 1];
      const lat1 = (p1[0] * Math.PI) / 180;
      const lat2 = (p2[0] * Math.PI) / 180;
      const lon1 = (p1[1] * Math.PI) / 180;
      const lon2 = (p2[1] * Math.PI) / 180;
      total += (lon2 - lon1) * (2 + Math.sin(lat1) + Math.sin(lat2));
    }
    return Math.abs((total * R * R) / 2.0);
  };

  // Haversine Perimeter Calculation in meters
  const calculatePerimeterM = (pts: [number, number][]): number => {
    if (pts.length < 2) return 0;
    const R = 6378137.0;
    let perimeter = 0;
    const ring = [...pts];
    if (ring[0][0] !== ring[ring.length - 1][0] || ring[0][1] !== ring[ring.length - 1][1]) {
      ring.push(ring[0]);
    }
    for (let i = 0; i < ring.length - 1; i++) {
      const p1 = ring[i];
      const p2 = ring[i + 1];
      const dLat = ((p2[0] - p1[0]) * Math.PI) / 180;
      const dLon = ((p2[1] - p1[1]) * Math.PI) / 180;
      const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos((p1[0] * Math.PI) / 180) * Math.cos((p2[0] * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      perimeter += R * c;
    }
    return perimeter;
  };

  const calculatedM2 = calculateGeodesicAreaM2(vertices);
  const calculatedPerimeterM = calculatePerimeterM(vertices);

  // Conversion helpers
  const m2ToAcres = (m2: number) => m2 / 4046.8564;
  const m2ToHectares = (m2: number) => m2 / 10000.0;
  const m2ToBigha = (m2: number) => m2 / 1337.8;

  const calculatedAcres = m2ToAcres(calculatedM2);
  const calculatedHa = m2ToHectares(calculatedM2);
  const calculatedBigha = m2ToBigha(calculatedM2);

  // Centroid
  const centroidLat = vertices.length > 0 ? vertices.reduce((sum, v) => sum + v[0], 0) / vertices.length : centerLat;
  const centroidLng = vertices.length > 0 ? vertices.reduce((sum, v) => sum + v[1], 0) / vertices.length : centerLng;

  // Percentage Difference
  let manualM2 = manualArea * 4046.8564;
  if (areaUnit === 'hectare' || areaUnit === 'ha') manualM2 = manualArea * 10000.0;
  if (areaUnit === 'bigha') manualM2 = manualArea * 1337.8;

  const pctDiff =
    calculatedM2 > 0 && manualM2 > 0
      ? (Math.abs(calculatedM2 - manualM2) / ((calculatedM2 + manualM2) / 2)) * 100
      : 0;

  // Map tile coordinate calculations
  const lat2tile = (lat: number, z: number) =>
    ((1 - Math.log(Math.tan((lat * Math.PI) / 180) + 1 / Math.cos((lat * Math.PI) / 180)) / Math.PI) / 2) * Math.pow(2, z);
  const lon2tile = (lon: number, z: number) => ((lon + 180) / 360) * Math.pow(2, z);

  const tileX = Math.floor(lon2tile(centerLng, zoom));
  const tileY = Math.floor(lat2tile(centerLat, zoom));

  const degreesPerPixelLng = 360 / (256 * Math.pow(2, zoom));
  const degreesPerPixelLat = (360 / (256 * Math.pow(2, zoom))) * Math.cos((centerLat * Math.PI) / 180);

  // Convert lat/lng to pixel offset relative to center
  const getPixelCoord = (lat: number, lng: number) => {
    const x = (lng - centerLng) / degreesPerPixelLng;
    const y = -(lat - centerLat) / degreesPerPixelLat;
    return { x: 384 + x, y: 192 + y }; // Center is at (384, 192) inside 768x384 container
  };

  const handleMapClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!mapRef.current) return;
    const rect = mapRef.current.getBoundingClientRect();
    const offsetX = e.clientX - rect.left - rect.width / 2;
    const offsetY = e.clientY - rect.top - rect.height / 2;

    const clickedLng = centerLng + offsetX * degreesPerPixelLng;
    const clickedLat = centerLat - offsetY * degreesPerPixelLat;

    setVertices((prev) => [...prev, [clickedLat, clickedLng]]);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      setSearchResults(data || []);
      if (data && data.length > 0) {
        const top = data[0];
        const newLat = parseFloat(top.lat);
        const newLng = parseFloat(top.lon);
        setCenterLat(newLat);
        setCenterLng(newLng);
        setZoom(16);
      }
    } catch (err) {
      console.warn('Location search error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleLocateMe = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCenterLat(pos.coords.latitude);
          setCenterLng(pos.coords.longitude);
          setZoom(17);
        },
        (err) => console.warn('Geolocation error:', err)
      );
    }
  };

  const handleSaveField = async () => {
    setIsSaving(true);
    try {
      const geojsonPolygon =
        vertices.length >= 3
          ? {
              type: 'Polygon',
              coordinates: [vertices.map(([lat, lng]) => [lng, lat])],
            }
          : null;

      const displayArea = vertices.length >= 3 ? parseFloat(calculatedAcres.toFixed(2)) : manualArea;

      await onSave({
        farm_id: farmId,
        field_name: fieldName,
        area_value: displayArea,
        area_unit: vertices.length >= 3 ? 'acre' : areaUnit,
        latitude: centroidLat,
        longitude: centroidLng,
        boundary_geojson: geojsonPolygon,
        perimeter_m: calculatedPerimeterM,
        centroid_lat: centroidLat,
        centroid_lng: centroidLng,
        geometry_source: vertices.length >= 3 ? 'GEOMETRIC' : 'MANUAL',
      });
    } catch (err) {
      console.error('Error saving field boundary:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const tilesToRender = [];
  for (let dx = -2; dx <= 2; dx++) {
    for (let dy = -1; dy <= 1; dy++) {
      const x = tileX + dx;
      const y = tileY + dy;
      let url = `https://tile.openstreetmap.org/${zoom}/${x}/${y}.png`;
      if (mapMode === 'satellite') {
        url = `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${zoom}/${y}/${x}`;
      }
      tilesToRender.push({ x: dx, y: dy, url, key: `${x}-${y}-${zoom}-${mapMode}` });
    }
  }

  // Generate SVG polygon points string
  const svgPolyPoints = vertices
    .map((v) => {
      const p = getPixelCoord(v[0], v[1]);
      return `${p.x},${p.y}`;
    })
    .join(' ');

  return (
    <div className="p-6 rounded-3xl bg-[#0B1C10] text-[#FAFBF7] border border-white/10 shadow-2xl space-y-6">
      {/* Header & Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Badge variant="lime">FIELD MAPPING WORKSPACE</Badge>
            <span className="text-xs text-white/60">GeoSpatial Field Boundary Polygon Engine</span>
          </div>
          <h3 className="text-2xl font-extrabold font-editorial text-white mt-1">
            Draw Real Field Boundaries
          </h3>
        </div>

        {/* Map View Mode & Locator Controls */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setMapMode(mapMode === 'standard' ? 'satellite' : 'standard')}
            className="px-3.5 py-2 rounded-2xl bg-white/10 hover:bg-white/20 text-xs font-bold text-[#D4E768] flex items-center gap-2 transition-all border border-white/10"
          >
            <Layers className="w-4 h-4" />
            {mapMode === 'satellite' ? 'Satellite Imagery' : 'Road / Map View'}
          </button>

          <button
            type="button"
            onClick={handleLocateMe}
            className="p-2 rounded-2xl bg-[#D4E768] text-[#0B1C10] font-bold text-xs hover:bg-[#c3d853] transition-all flex items-center gap-1.5"
            title="Use current GPS location"
          >
            <LocateFixed className="w-4 h-4" />
            Locate Me
          </button>
        </div>
      </div>

      {/* Location Search Bar */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-white/40 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search village, pin code, post office, or location..."
            className="w-full pl-10 pr-4 py-2.5 rounded-2xl bg-white/10 text-white text-xs font-medium placeholder-white/40 border border-white/15 focus:outline-none focus:border-[#D4E768]"
          />
        </div>
        <Button type="submit" variant="lime" size="sm" disabled={isSearching}>
          {isSearching ? 'Searching...' : 'Search'}
        </Button>
      </form>

      {/* Main Interactive Field Map Canvas */}
      <div
        ref={mapRef}
        onClick={handleMapClick}
        className="relative w-full h-[380px] rounded-3xl overflow-hidden bg-[#112316] border border-white/20 shadow-inner cursor-crosshair select-none group"
      >
        {/* Map Tiles Layer */}
        <div className="absolute inset-0 flex items-center justify-center overflow-hidden pointer-events-none">
          <div className="relative w-[768px] h-[384px] flex items-center justify-center">
            {tilesToRender.map((tile) => (
              <img
                key={tile.key}
                src={tile.url}
                alt="Map Tile"
                className="absolute w-[256px] h-[256px] opacity-90 contrast-[1.05] brightness-[0.95]"
                style={{
                  transform: `translate(${tile.x * 256}px, ${tile.y * 256}px)`,
                }}
              />
            ))}
          </div>
        </div>

        {/* SVG Polygon Boundary & Vertices Overlay */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
          {vertices.length >= 3 && (
            <polygon
              points={svgPolyPoints}
              fill="rgba(212, 231, 104, 0.25)"
              stroke="#D4E768"
              strokeWidth="2.5"
              strokeDasharray="4 2"
            />
          )}
          {vertices.length >= 2 && vertices.length < 3 && (
            <polyline
              points={svgPolyPoints}
              stroke="#D4E768"
              strokeWidth="2"
            />
          )}

          {vertices.map((v, idx) => {
            const p = getPixelCoord(v[0], v[1]);
            return (
              <g key={idx}>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r="7"
                  fill="#0B1C10"
                  stroke="#D4E768"
                  strokeWidth="2.5"
                />
                <text
                  x={p.x + 10}
                  y={p.y + 4}
                  fill="#D4E768"
                  fontSize="10"
                  fontWeight="bold"
                  fontFamily="sans-serif"
                >
                  P{idx + 1}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Instructions Badge Overlay */}
        <div className="absolute top-3 left-3 bg-[#0B1C10]/90 backdrop-blur-md px-3.5 py-2 rounded-full border border-white/20 text-[11px] font-semibold text-[#D4E768] flex items-center gap-2 pointer-events-none z-20 shadow-lg">
          <Navigation className="w-3.5 h-3.5 text-[#D4E768]" />
          <span>
            {vertices.length === 0
              ? 'Click anywhere on map to start placing field boundary points'
              : vertices.length < 3
              ? `Place ${3 - vertices.length} more point(s) to close the field polygon`
              : `Field polygon complete (${vertices.length} boundary points placed)`}
          </span>
        </div>

        {/* Map Zoom Controls */}
        <div className="absolute bottom-3 right-3 flex flex-col gap-2 z-20">
          <div className="flex flex-col rounded-2xl bg-[#0B1C10]/90 border border-white/20 shadow-lg overflow-hidden">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setZoom((z) => Math.min(19, z + 1));
              }}
              className="w-10 h-9 flex items-center justify-center text-white hover:bg-white/10 border-b border-white/10"
              title="Zoom In"
            >
              <Plus className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setZoom((z) => Math.max(4, z - 1));
              }}
              className="w-10 h-9 flex items-center justify-center text-white hover:bg-white/10"
              title="Zoom Out"
            >
              <Minus className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Boundary Tools Overlay */}
        <div className="absolute bottom-3 left-3 flex gap-2 z-20">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setVertices([]);
            }}
            disabled={vertices.length === 0}
            className="px-3 py-1.5 rounded-2xl bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 text-xs font-semibold border border-rose-500/30 flex items-center gap-1.5 transition-all disabled:opacity-40"
          >
            <Trash2 className="w-3.5 h-3.5" /> Redraw / Clear
          </button>
        </div>
      </div>

      {/* Real-time Field Metrics Panel */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-white/5 p-4 rounded-3xl border border-white/10 text-xs">
        <div>
          <span className="text-white/60 block text-[10px] uppercase font-bold">Calculated Area</span>
          <strong className="text-lg font-extrabold text-[#D4E768] font-mono">
            {vertices.length >= 3 ? `${calculatedAcres.toFixed(2)} acres` : '0.00 acres'}
          </strong>
          <p className="text-[10px] text-white/50">
            {vertices.length >= 3 ? `${calculatedHa.toFixed(2)} ha • ${calculatedBigha.toFixed(2)} bigha • ${calculatedM2.toLocaleString()} m²` : 'Draw boundary on map'}
          </p>
        </div>

        <div>
          <span className="text-white/60 block text-[10px] uppercase font-bold">Perimeter Length</span>
          <strong className="text-base font-extrabold text-white font-mono">
            {calculatedPerimeterM > 0 ? `${calculatedPerimeterM.toFixed(1)} meters` : '0 m'}
          </strong>
          <p className="text-[10px] text-white/50">Field boundary outline</p>
        </div>

        <div>
          <span className="text-white/60 block text-[10px] uppercase font-bold">Centroid Coordinates</span>
          <strong className="text-base font-extrabold text-white font-mono">
            {centroidLat.toFixed(4)}° N, {centroidLng.toFixed(4)}° E
          </strong>
          <p className="text-[10px] text-white/50">Geographic Center</p>
        </div>

        <div>
          <span className="text-white/60 block text-[10px] uppercase font-bold">Geometry Source</span>
          <Badge variant={vertices.length >= 3 ? 'success' : 'warning'}>
            {vertices.length >= 3 ? 'GEOMETRIC (Polygon derived)' : 'MANUAL (Declared)'}
          </Badge>
          {vertices.length >= 3 && pctDiff > 0 && (
            <p className="text-[10px] text-amber-300 mt-1">
              Diff with manual: {pctDiff.toFixed(1)}%
            </p>
          )}
        </div>
      </div>

      {/* Field Details Form Inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-white/10">
        <div>
          <label className="block text-xs font-bold text-white/80 mb-1">Field Name</label>
          <input
            type="text"
            value={fieldName}
            onChange={(e) => setFieldName(e.target.value)}
            className="w-full px-4 py-2.5 rounded-2xl bg-white/10 text-white text-xs font-semibold border border-white/15 focus:outline-none focus:border-[#D4E768]"
            placeholder="e.g. North Field"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-white/80 mb-1">Manual Declared Area</label>
          <input
            type="number"
            step="0.01"
            value={manualArea}
            onChange={(e) => setManualArea(parseFloat(e.target.value) || 0)}
            className="w-full px-4 py-2.5 rounded-2xl bg-white/10 text-white text-xs font-semibold border border-white/15 focus:outline-none focus:border-[#D4E768]"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-white/80 mb-1">Area Unit</label>
          <select
            value={areaUnit}
            onChange={(e) => setAreaUnit(e.target.value)}
            className="w-full px-4 py-2.5 rounded-2xl bg-[#0B1C10] text-white text-xs font-semibold border border-white/15 focus:outline-none focus:border-[#D4E768]"
          >
            <option value="acre">Acres</option>
            <option value="hectare">Hectares</option>
            <option value="bigha">Bighas</option>
            <option value="sqm">Square Meters (m²)</option>
          </select>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
        <Button onClick={onCancel} variant="secondary" size="sm">
          Cancel
        </Button>
        <Button
          onClick={handleSaveField}
          variant="lime"
          size="sm"
          disabled={isSaving}
          icon={<Check className="w-4 h-4" />}
        >
          {isSaving ? 'Saving Field...' : 'Save Field Boundary'}
        </Button>
      </div>
    </div>
  );
};
