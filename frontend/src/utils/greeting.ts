import { useState, useEffect } from 'react';

/**
 * Generates a dynamic, time-aware greeting based on local or preferred timezone.
 * Rules:
 * 05:00–11:59: Good morning
 * 12:00–16:59: Good afternoon
 * 17:00–20:59: Good evening
 * 21:00–04:59: Good night
 */
export function getTimeAwareGreeting(timezone?: string): string {
  try {
    const tz = timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    const formatter = new Intl.DateTimeFormat([], {
      timeZone: tz,
      hour: 'numeric',
      hour12: false,
    });
    const hourStr = formatter.format(new Date());
    const hour = parseInt(hourStr, 10);

    if (hour >= 5 && hour < 12) return 'Good morning';
    if (hour >= 12 && hour < 17) return 'Good afternoon';
    if (hour >= 17 && hour < 21) return 'Good evening';
    return 'Good night';
  } catch {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return 'Good morning';
    if (hour >= 12 && hour < 17) return 'Good afternoon';
    if (hour >= 17 && hour < 21) return 'Good evening';
    return 'Good night';
  }
}

/**
 * Resolves the display name for farmer greeting.
 * Priority:
 * 1. farmerProfile.full_name
 * 2. authenticatedUser.name / full_name
 * 3. authenticatedUser.email prefix
 * 4. Generic "Farmer"
 */
export function getGreetingDisplayName(
  farmerProfile?: { full_name?: string } | null,
  user?: { name?: string; full_name?: string; email?: string } | null
): string {
  const fullName = farmerProfile?.full_name || user?.full_name || user?.name;
  if (
    fullName &&
    fullName.trim() &&
    fullName !== 'Default Farmer' &&
    fullName !== 'Farmer User' &&
    fullName !== 'Farmer'
  ) {
    const parts = fullName.trim().split(' ');
    return parts[0];
  }
  if (user?.email && user.email.includes('@')) {
    const prefix = user.email.split('@')[0];
    if (prefix && prefix !== 'farmer' && prefix !== 'default_user') {
      return prefix;
    }
  }
  return 'Farmer';
}

/**
 * Generates dynamic avatar initials from the canonical farmer profile.
 * E.g. "Animesh Sahoo" -> "AS", "Animesh" -> "A".
 */
export function getAvatarInitials(
  farmerProfile?: { full_name?: string } | null,
  user?: { name?: string; full_name?: string; email?: string } | null
): string {
  const fullName = farmerProfile?.full_name || user?.full_name || user?.name;
  if (
    fullName &&
    fullName.trim() &&
    fullName !== 'Default Farmer' &&
    fullName !== 'Farmer User'
  ) {
    const parts = fullName.trim().split(' ').filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    } else if (parts.length === 1) {
      return parts[0][0].toUpperCase();
    }
  }
  if (user?.email) {
    return user.email.charAt(0).toUpperCase();
  }
  return 'F';
}

/**
 * Custom React Hook for live dynamic time-aware greeting.
 * Recalculates on window focus and minute intervals so greeting updates seamlessly across boundaries.
 */
export function useGreeting(
  farmerProfile?: { full_name?: string; timezone?: string } | null,
  user?: { name?: string; full_name?: string; email?: string } | null
) {
  const [greeting, setGreeting] = useState(() => getTimeAwareGreeting(farmerProfile?.timezone));
  const displayName = getGreetingDisplayName(farmerProfile, user);
  const avatarInitials = getAvatarInitials(farmerProfile, user);

  useEffect(() => {
    const update = () => {
      setGreeting(getTimeAwareGreeting(farmerProfile?.timezone));
    };
    update();
    const interval = setInterval(update, 60000); // Recalculate every 60 seconds
    window.addEventListener('focus', update);
    return () => {
      clearInterval(interval);
      window.removeEventListener('focus', update);
    };
  }, [farmerProfile?.timezone]);

  return {
    greeting,
    displayName,
    avatarInitials,
    fullGreeting: `${greeting}, ${displayName}.`,
  };
}
