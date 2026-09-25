import React, { useState } from 'react';
import { ImageOff, ExternalLink, ShieldCheck } from 'lucide-react';
import { SmartCropRecommendationItem } from '../../types/api';
import { getCropImageMetadata } from '../../utils/cropImageMap';

interface CropImageProps {
  crop: SmartCropRecommendationItem;
  className?: string;
  showAttribution?: boolean;
  aspectRatio?: 'landscape' | 'square' | 'auto';
}

export const CropImage: React.FC<CropImageProps> = ({
  crop,
  className = '',
  showAttribution = true,
  aspectRatio = 'landscape',
}) => {
  const [hasError, setHasError] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // 1. Check dynamic API image first
  const apiImage = crop.image;

  // 2. Local verified asset fallback mapping
  const localMeta = getCropImageMetadata(crop.crop);

  // Determine effective image URL
  const imageUrl = (!hasError && apiImage?.available && apiImage.url)
    ? apiImage.url
    : (!hasError ? localMeta.imagePath : null);

  const altText = apiImage?.alt || localMeta.altText || `${crop.display_name} crop photography`;
  const provider = apiImage?.provider || (localMeta.isSpecific ? 'AgriNexus Verified Asset' : null);
  const author = apiImage?.author || (localMeta.isSpecific ? localMeta.attribution : null);
  const license = apiImage?.license;
  const licenseUrl = apiImage?.license_url;
  const sourceUrl = apiImage?.source_url;

  const isImageAvailable = Boolean(imageUrl && !hasError);

  const aspectClass = aspectRatio === 'square'
    ? 'aspect-square'
    : aspectRatio === 'landscape'
    ? 'aspect-16/9 lg:aspect-4/3'
    : '';

  return (
    <div className={`relative overflow-hidden bg-[#0B1C10] ${aspectClass} ${className}`}>
      {/* Loading Skeleton */}
      {isLoading && isImageAvailable && (
        <div className="absolute inset-0 z-10 bg-slate-800 animate-pulse flex items-center justify-center text-slate-500 text-xs font-mono">
          <span>Resolving Species Image...</span>
        </div>
      )}

      {/* Main Image Rendering */}
      {isImageAvailable ? (
        <img
          src={imageUrl!}
          alt={altText}
          loading="lazy"
          onLoad={() => setIsLoading(false)}
          onError={() => {
            setHasError(true);
            setIsLoading(false);
          }}
          className={`w-full h-full object-cover object-center transition-all duration-700 ${
            isLoading ? 'opacity-0 scale-95' : 'opacity-85 group-hover:scale-105'
          }`}
        />
      ) : (
        /* Controlled Missing-Image / Image Unavailable State */
        <div className="w-full h-full flex flex-col items-center justify-center p-6 text-center bg-gradient-to-br from-[#122417] via-[#0B1C10] to-[#1A3320] text-slate-300 space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-white/10 border border-white/15 flex items-center justify-center text-[#D4E768] shadow-sm">
            <ImageOff className="w-6 h-6" />
          </div>
          <div className="space-y-1 max-w-xs">
            <span className="text-xs font-extrabold uppercase tracking-wider text-[#D4E768] block">
              Image Unavailable
            </span>
            <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
              No verified photo meeting relevance threshold for <strong className="text-white">{crop.display_name}</strong>.
            </p>
          </div>
        </div>
      )}

      {/* Gradient Vignette Overlay for Text Legibility */}
      {isImageAvailable && (
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#0B1C10] via-transparent to-black/20" />
      )}

      {/* Attribution & Provider Overlay */}
      {showAttribution && isImageAvailable && (provider || author) && (
        <div className="absolute bottom-2 right-2 z-20 max-w-[85%] bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-lg border border-white/15 text-[10px] text-slate-300 flex items-center gap-1.5 truncate">
          <ShieldCheck className="w-3 h-3 text-[#D4E768] shrink-0" />
          <span className="truncate">
            {author || provider}
          </span>
          {sourceUrl && (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noreferrer"
              className="text-[#D4E768] hover:underline shrink-0"
              title="View original image source"
            >
              <ExternalLink className="w-2.5 h-2.5 inline" />
            </a>
          )}
        </div>
      )}
    </div>
  );
};
