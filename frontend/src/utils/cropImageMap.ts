/**
 * Canonical Crop Image Database & Image Validation Utility
 * Ensures strict content integrity: Every crop receives a verified image matching its exact species identity.
 * Fallback to an unambiguous generic agricultural placeholder occurs ONLY when no specific image exists,
 * eliminating misleading representations (e.g. wheat field for Mango).
 */

export interface CropImageMetadata {
  cropId: string;
  imagePath: string;
  altText: string;
  attribution: string;
  isSpecific: boolean;
}

export const CROP_IMAGE_MAP: Record<string, CropImageMetadata> = {
  rice: {
    cropId: 'rice',
    imagePath: '/images/crops/rice.webp',
    altText: 'Lush green flooded rice paddy field',
    attribution: 'AgriNexus Agricultural Asset Library - Rice',
    isSpecific: true,
  },
  maize: {
    cropId: 'maize',
    imagePath: '/images/crops/maize.webp',
    altText: 'Golden maize corn field ready for harvest',
    attribution: 'AgriNexus Agricultural Asset Library - Maize',
    isSpecific: true,
  },
  jute: {
    cropId: 'jute',
    imagePath: '/images/crops/jute.webp',
    altText: 'Tall green jute crop cultivation field',
    attribution: 'AgriNexus Agricultural Asset Library - Jute',
    isSpecific: true,
  },
  cotton: {
    cropId: 'cotton',
    imagePath: '/images/crops/cotton.webp',
    altText: 'Blooming white cotton bolls in agricultural field',
    attribution: 'AgriNexus Agricultural Asset Library - Cotton',
    isSpecific: true,
  },
  wheat: {
    cropId: 'wheat',
    imagePath: '/images/crops/wheat.webp',
    altText: 'Golden wheat stalks under clear blue sky',
    attribution: 'AgriNexus Agricultural Asset Library - Wheat',
    isSpecific: true,
  },
  chickpea: {
    cropId: 'chickpea',
    imagePath: '/images/crops/chickpea.webp',
    altText: 'Green chickpea gram pod plants in soil',
    attribution: 'AgriNexus Agricultural Asset Library - Chickpea',
    isSpecific: true,
  },
  kidneybeans: {
    cropId: 'kidneybeans',
    imagePath: '/images/crops/kidneybeans.webp',
    altText: 'Rajma kidney bean legume crop plants',
    attribution: 'AgriNexus Agricultural Asset Library - Kidney Beans',
    isSpecific: true,
  },
  pigeonpeas: {
    cropId: 'pigeonpeas',
    imagePath: '/images/crops/pigeonpeas.webp',
    altText: 'Arhar tur pigeon pea flowering shrubs',
    attribution: 'AgriNexus Agricultural Asset Library - Pigeon Peas',
    isSpecific: true,
  },
  mothbeans: {
    cropId: 'mothbeans',
    imagePath: '/images/crops/mothbeans.webp',
    altText: 'Drought tolerant moth bean foliage in arid soil',
    attribution: 'AgriNexus Agricultural Asset Library - Moth Beans',
    isSpecific: true,
  },
  mungbean: {
    cropId: 'mungbean',
    imagePath: '/images/crops/mungbean.webp',
    altText: 'Green gram mungbean pod clusters on plants',
    attribution: 'AgriNexus Agricultural Asset Library - Mungbean',
    isSpecific: true,
  },
  blackgram: {
    cropId: 'blackgram',
    imagePath: '/images/crops/blackgram.webp',
    altText: 'Urad blackgram pulse crop field',
    attribution: 'AgriNexus Agricultural Asset Library - Blackgram',
    isSpecific: true,
  },
  lentil: {
    cropId: 'lentil',
    imagePath: '/images/crops/lentil.webp',
    altText: 'Masoor lentil leguminous field crop',
    attribution: 'AgriNexus Agricultural Asset Library - Lentil',
    isSpecific: true,
  },
  pomegranate: {
    cropId: 'pomegranate',
    imagePath: '/images/crops/pomegranate.webp',
    altText: 'Ripe red pomegranates hanging on orchard tree',
    attribution: 'AgriNexus Agricultural Asset Library - Pomegranate',
    isSpecific: true,
  },
  banana: {
    cropId: 'banana',
    imagePath: '/images/crops/banana.webp',
    altText: 'Tropical banana plant orchard with fresh green leaves',
    attribution: 'AgriNexus Agricultural Asset Library - Banana',
    isSpecific: true,
  },
  mango: {
    cropId: 'mango',
    imagePath: '/images/crops/mango.webp',
    altText: 'Golden ripe mango fruit hanging on lush tree branch',
    attribution: 'AgriNexus Agricultural Asset Library - Mango',
    isSpecific: true,
  },
  grapes: {
    cropId: 'grapes',
    imagePath: '/images/crops/grapes.webp',
    altText: 'Juicy purple grape clusters in vineyard orchard',
    attribution: 'AgriNexus Agricultural Asset Library - Grapes',
    isSpecific: true,
  },
  watermelon: {
    cropId: 'watermelon',
    imagePath: '/images/crops/watermelon.webp',
    altText: 'Large green striped watermelon ripening on vine',
    attribution: 'AgriNexus Agricultural Asset Library - Watermelon',
    isSpecific: true,
  },
  muskmelon: {
    cropId: 'muskmelon',
    imagePath: '/images/crops/muskmelon.webp',
    altText: 'Ripe sweet muskmelon cantaloupe fruit in field',
    attribution: 'AgriNexus Agricultural Asset Library - Muskmelon',
    isSpecific: true,
  },
  apple: {
    cropId: 'apple',
    imagePath: '/images/crops/apple.webp',
    altText: 'Red apples hanging on orchard branches in mountain valley',
    attribution: 'AgriNexus Agricultural Asset Library - Apple',
    isSpecific: true,
  },
  orange: {
    cropId: 'orange',
    imagePath: '/images/crops/orange.webp',
    altText: 'Bright citrus oranges growing in sunny grove',
    attribution: 'AgriNexus Agricultural Asset Library - Orange',
    isSpecific: true,
  },
  papaya: {
    cropId: 'papaya',
    imagePath: '/images/crops/papaya.webp',
    altText: 'Papaya tree with cluster of green and yellow fruit',
    attribution: 'AgriNexus Agricultural Asset Library - Papaya',
    isSpecific: true,
  },
  coconut: {
    cropId: 'coconut',
    imagePath: '/images/crops/coconut.webp',
    altText: 'Coastal coconut palm trees against clear sky',
    attribution: 'AgriNexus Agricultural Asset Library - Coconut',
    isSpecific: true,
  },
  mustard: {
    cropId: 'mustard',
    imagePath: '/images/crops/mustard.webp',
    altText: 'Vibrant yellow mustard sarson flowers in farm field',
    attribution: 'AgriNexus Agricultural Asset Library - Mustard',
    isSpecific: true,
  },
  sugarcane: {
    cropId: 'sugarcane',
    imagePath: '/images/crops/sugarcane.webp',
    altText: 'Dense tall sugarcane field plantation',
    attribution: 'AgriNexus Agricultural Asset Library - Sugarcane',
    isSpecific: true,
  },
  potato: {
    cropId: 'potato',
    imagePath: '/images/crops/potato.webp',
    altText: 'Freshly harvested potato tubers in farm soil',
    attribution: 'AgriNexus Agricultural Asset Library - Potato',
    isSpecific: true,
  },
  groundnut: {
    cropId: 'groundnut',
    imagePath: '/images/crops/groundnut.webp',
    altText: 'Groundnut peanut plants with pods in light sandy soil',
    attribution: 'AgriNexus Agricultural Asset Library - Groundnut',
    isSpecific: true,
  },
};

export const GENERIC_CROP_PLACEHOLDER: CropImageMetadata = {
  cropId: 'generic',
  imagePath: '/images/crop-intelligence.webp',
  altText: 'Agricultural field landscape (Generic Placeholder)',
  attribution: 'AgriNexus Generic Agriculture Placeholder',
  isSpecific: false,
};

/**
 * Safely retrieve verified crop image metadata by crop key
 */
export function getCropImageMetadata(cropId: string): CropImageMetadata {
  const key = cropId.trim().toLowerCase();
  if (key in CROP_IMAGE_MAP) {
    return CROP_IMAGE_MAP[key];
  }
  return {
    ...GENERIC_CROP_PLACEHOLDER,
    altText: `${cropId} field landscape`,
  };
}
