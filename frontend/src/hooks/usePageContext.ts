import { useLocation } from 'react-router-dom';
import { useLocationContext } from '../context/LocationContext';
import { useFarmerProfile } from '../context/FarmerProfileContext';
import type { PageContext } from '../types/assistant';

const ROUTE_NAME_MAP: Record<string, string> = {
  '/': 'Farm Command Center',
  '/dashboard': 'Farm Command Center',
  '/weather': 'Weather Intelligence',
  '/crop': 'Crop Recommendation',
  '/irrigation': 'Irrigation Intelligence',
  '/market': 'Market Intelligence',
  '/disease': 'Disease Detection',
  '/pest': 'Pest Risk & Visual Identification',
  '/soil': 'Soil Analysis',
  '/yield': 'Yield Prediction',
  '/crop-calendar': 'Crop Calendar',
  '/fertilizer': 'Fertilizer Intelligence',
  '/live': 'Live Vision Stream',
  '/profile': 'Farmer Profile',
};

export function usePageContext(): PageContext {
  const locationState = useLocation();
  const pathname = locationState.pathname;

  let pageName = ROUTE_NAME_MAP[pathname];
  if (!pageName) {
    // Fallback for nested or unknown routes
    const clean = pathname.replace(/^\//, '').replace(/-/g, ' ');
    pageName = clean ? clean.charAt(0).toUpperCase() + clean.slice(1) : 'Farm Command Center';
  }

  let userLocation: PageContext['selected_location'] = undefined;
  try {
    const { location } = useLocationContext();
    if (location) {
      userLocation = {
        latitude: location.latitude,
        longitude: location.longitude,
        displayName: location.displayName,
      };
    }
  } catch {
    // Context unmounted
  }

  let selectedFieldId: number | undefined = undefined;
  let selectedFieldName: string | undefined = undefined;
  let selectedCropId: number | undefined = undefined;
  let selectedCropName: string | undefined = undefined;

  try {
    const { selectedField, selectedCrop } = useFarmerProfile();
    if (selectedField) {
      selectedFieldId = selectedField.id;
      selectedFieldName = selectedField.field_name;
    }
    if (selectedCrop) {
      selectedCropId = selectedCrop.id;
      selectedCropName = selectedCrop.crop_name;
    }
  } catch {
    // Context unmounted
  }

  return {
    route: pathname,
    page_name: pageName,
    selected_field_id: selectedFieldId,
    selected_field_name: selectedFieldName,
    selected_crop_id: selectedCropId,
    selected_crop_name: selectedCropName,
    selected_location: userLocation,
  };
}
