import React from 'react';
import { CATEGORY_OPTIONS, CROP_GROUP_COLORS, DEFAULT_CROP_COLOR, type CategoryKey } from '../config/globals';

type LegendProps = {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  shape?: 'circle' | 'square';
  items?: CategoryKey[];
  title?: string;
  className?: string;
  style?: React.CSSProperties;
  widthPx?: number;
};

const cornerStyle: Record<NonNullable<LegendProps['position']>, React.CSSProperties> = {
  'top-right':    { top: 12, right: 12 },
  'top-left':     { top: 12, left: 12 },
  'bottom-right': { bottom: 12, right: 12 },
  'bottom-left':  { bottom: 12, left: 12 },
};

const Legend: React.FC<LegendProps> = ({
  position = 'top-right',
  shape = 'circle',
  items,
  title = 'Legend',
  className,
  style,
  widthPx = 220,
}) => {
  const list = (items ?? CATEGORY_OPTIONS.map(o => o.key)).map((key) => ({
    key,
    label: CATEGORY_OPTIONS.find(o => o.key === key)?.label ?? key,
    color: CROP_GROUP_COLORS[key] ?? DEFAULT_CROP_COLOR,
  }));

  return (
    <div
      className={className ? `ss-legend ${className}` : 'ss-legend'}
      style={{
        position: 'absolute',
        zIndex: 1000,
        ...cornerStyle[position],
        ...style,
      }}
    >
      <div
        style={{
          width: widthPx,
          background: 'rgba(255,255,255,0.95)',
          backdropFilter: 'blur(2px)',
          borderRadius: 10,
          boxShadow: '0 6px 16px rgba(0,0,0,0.15)',
          padding: 12,
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>{title}</div>
        <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
          {list.map(({ key, label, color }) => (
            <li
              key={key}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                marginBottom: 6,
              }}
            >
              <span
                aria-hidden
                style={{
                  display: 'inline-block',
                  width: 12,
                  height: 12,
                  background: color,
                  border: '1px solid rgba(0,0,0,0.25)',
                  borderRadius: shape === 'circle' ? '9999px' : 3,
                  flex: '0 0 auto',
                }}
              />
              <span style={{ fontSize: 13, lineHeight: 1.2 }}>{label}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Legend;
