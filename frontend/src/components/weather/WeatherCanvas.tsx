import React, { useEffect, useRef } from 'react';
import { WeatherIntensityParameters } from '../../types/weatherVisualization';

interface WeatherCanvasProps {
  intensity: WeatherIntensityParameters;
}

interface RainParticle {
  x: number;
  y: number;
  length: number;
  speed: number;
  opacity: number;
}

interface SplashParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  maxLife: number;
  opacity: number;
}

interface SnowParticle {
  x: number;
  y: number;
  radius: number;
  speed: number;
  drift: number;
  opacity: number;
}

interface WindParticle {
  x: number;
  y: number;
  length: number;
  speed: number;
  opacity: number;
}

export const WeatherCanvas: React.FC<WeatherCanvasProps> = ({ intensity }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameIdRef = useRef<number | null>(null);

  // Intensity ref so loop accesses latest intensity without re-binding loop
  const intensityRef = useRef<WeatherIntensityParameters>(intensity);
  useEffect(() => {
    intensityRef.current = intensity;
  }, [intensity]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Canvas size handling
    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || window.innerHeight);

    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };

    window.addEventListener('resize', handleResize);

    // Particles collections stored in closure / ref (NOT React state)
    let raindrops: RainParticle[] = [];
    let splashes: SplashParticle[] = [];
    let snowflakes: SnowParticle[] = [];
    let windLines: WindParticle[] = [];

    // Initialize particles
    const initParticles = () => {
      const currentInt = intensityRef.current;
      const countScale = prefersReducedMotion ? 0.3 : 1.0;

      // Rain particles
      const targetRainCount = Math.floor(currentInt.rainIntensity * 250 * countScale);
      raindrops = Array.from({ length: targetRainCount }, () => ({
        x: Math.random() * (width + 200) - 100,
        y: Math.random() * height,
        length: 12 + Math.random() * 18 * currentInt.rainIntensity,
        speed: (12 + Math.random() * 14) * (prefersReducedMotion ? 0.4 : 1.0),
        opacity: 0.2 + Math.random() * 0.5,
      }));

      // Snow particles
      const targetSnowCount = Math.floor(currentInt.snowIntensity * 120 * countScale);
      snowflakes = Array.from({ length: targetSnowCount }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        radius: 1.5 + Math.random() * 3.5,
        speed: (1.0 + Math.random() * 2.0) * (prefersReducedMotion ? 0.3 : 1.0),
        drift: (Math.random() - 0.5) * 0.8,
        opacity: 0.4 + Math.random() * 0.5,
      }));

      // Wind particles
      const targetWindCount = Math.floor(currentInt.windStrength * 40 * countScale);
      windLines = Array.from({ length: targetWindCount }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        length: 40 + Math.random() * 80,
        speed: (4 + Math.random() * 8) * (prefersReducedMotion ? 0.3 : 1.0),
        opacity: 0.05 + Math.random() * 0.15,
      }));
    };

    initParticles();

    // Lightning state
    let isLightningActive = false;
    let lightningOpacity = 0;

    // Animation Loop
    let lastTime = performance.now();

    const render = (time: number) => {
      const dt = Math.min(100, time - lastTime) / 1000;
      lastTime = time;

      ctx.clearRect(0, 0, width, height);

      const currentInt = intensityRef.current;
      const angleRad = ((currentInt.windDirection - 180) * Math.PI) / 180;
      const windDx = Math.sin(angleRad) * currentInt.windStrength * 12;

      // ----------------------------------------------------
      // 1. RAIN RENDERING & PHYSICS
      // ----------------------------------------------------
      if (currentInt.rainIntensity > 0) {
        ctx.strokeStyle = 'rgba(180, 215, 255, 0.6)';
        ctx.lineWidth = 1.2;
        ctx.beginPath();

        for (let i = 0; i < raindrops.length; i++) {
          const drop = raindrops[i];
          drop.y += drop.speed;
          drop.x += windDx;

          const endX = drop.x + windDx * 0.6;
          const endY = drop.y + drop.length;

          ctx.moveTo(drop.x, drop.y);
          ctx.lineTo(endX, endY);

          // Splash on floor collision
          if (drop.y >= height - 20) {
            if (
              !prefersReducedMotion &&
              currentInt.rainIntensity > 0.3 &&
              Math.random() < 0.25
            ) {
              for (let s = 0; s < 2; s++) {
                splashes.push({
                  x: drop.x,
                  y: height - 5 - Math.random() * 10,
                  vx: (Math.random() - 0.5) * 4,
                  vy: -1 - Math.random() * 3,
                  life: 0,
                  maxLife: 10 + Math.random() * 10,
                  opacity: 0.6,
                });
              }
            }
            drop.y = -drop.length;
            drop.x = Math.random() * (width + 200) - 100;
          }
        }
        ctx.stroke();

        // Render Rain Splashes
        if (splashes.length > 0) {
          ctx.fillStyle = 'rgba(200, 230, 255, 0.5)';
          for (let i = splashes.length - 1; i >= 0; i--) {
            const s = splashes[i];
            s.x += s.vx;
            s.y += s.vy;
            s.vy += 0.3; // Gravity
            s.life += 1;
            s.opacity = Math.max(0, 0.6 * (1 - s.life / s.maxLife));

            ctx.fillRect(s.x, s.y, 1.5, 1.5);

            if (s.life >= s.maxLife) {
              splashes.splice(i, 1);
            }
          }
        }
      }

      // ----------------------------------------------------
      // 2. SNOW RENDERING & PHYSICS
      // ----------------------------------------------------
      if (currentInt.snowIntensity > 0) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
        for (let i = 0; i < snowflakes.length; i++) {
          const flake = snowflakes[i];
          flake.y += flake.speed;
          flake.x += flake.drift + windDx * 0.3;

          ctx.beginPath();
          ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2);
          ctx.fill();

          if (flake.y > height) {
            flake.y = -10;
            flake.x = Math.random() * width;
          }
        }
      }

      // ----------------------------------------------------
      // 3. WIND VECTOR RENDERING
      // ----------------------------------------------------
      if (currentInt.windStrength > 0.2) {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
        ctx.lineWidth = 1;
        ctx.beginPath();

        for (let i = 0; i < windLines.length; i++) {
          const wLine = windLines[i];
          wLine.x += wLine.speed + Math.abs(windDx);
          wLine.y += windDx * 0.2;

          ctx.moveTo(wLine.x, wLine.y);
          ctx.lineTo(wLine.x + wLine.length, wLine.y + windDx * 0.5);

          if (wLine.x > width + 100) {
            wLine.x = -150;
            wLine.y = Math.random() * height;
          }
        }
        ctx.stroke();
      }

      // ----------------------------------------------------
      // 4. LIGHTNING FLASH (THUNDERSTORM)
      // ----------------------------------------------------
      if (!prefersReducedMotion && currentInt.lightningProbability > 0) {
        if (!isLightningActive && Math.random() < currentInt.lightningProbability) {
          isLightningActive = true;
          lightningOpacity = 0.4 + Math.random() * 0.4;
        }

        if (isLightningActive) {
          ctx.fillStyle = `rgba(255, 255, 255, ${lightningOpacity})`;
          ctx.fillRect(0, 0, width, height);
          lightningOpacity -= dt * 2.5;
          if (lightningOpacity <= 0) {
            isLightningActive = false;
          }
        }
      }

      animFrameIdRef.current = requestAnimationFrame(render);
    };

    animFrameIdRef.current = requestAnimationFrame(render);

    return () => {
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none z-10"
    />
  );
};
