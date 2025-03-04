import React from 'react';
import { SvgIcon, SvgIconProps } from '@mui/material';

// 导出favicon SVG路径数据
export const LogoIconPaths = {
  circle: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z",
  aiText: "M7 7h2v10H7V7zm4 0h2v10h-2V7zm4 0h2v10h-2V7z",
  border: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z",
};

// Favicon版本的Logo
export const FaviconLogo = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      width="64"
      height="64"
    >
      <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="30%" stopColor="#2196F3" />
          <stop offset="90%" stopColor="#21CBF3" />
        </linearGradient>
      </defs>
      <path d={LogoIconPaths.circle} fill="url(#gradient)" opacity="0.2" />
      <path d={LogoIconPaths.aiText} fill="url(#gradient)" />
      <path d={LogoIconPaths.border} fill="url(#gradient)" />
      <circle cx="12" cy="12" r="1" fill="url(#gradient)" />
      <circle cx="8" cy="12" r="1" fill="url(#gradient)" />
      <circle cx="16" cy="12" r="1" fill="url(#gradient)" />
    </svg>
  );
};

// 主Logo组件
const Logo = (props: SvgIconProps) => {
  return (
    <SvgIcon
      {...props}
      viewBox="0 0 24 24"
      sx={{
        width: props.width || '40px',
        height: props.height || '40px',
        ...props.sx
      }}
    >
      <defs>
        <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="30%" stopColor="#2196F3" />
          <stop offset="90%" stopColor="#21CBF3" />
        </linearGradient>
      </defs>
      <path
        d={LogoIconPaths.circle}
        fill="url(#logoGradient)"
        opacity="0.2"
      />
      <path
        d={LogoIconPaths.aiText}
        fill="url(#logoGradient)"
      />
      <path
        d={LogoIconPaths.border}
        fill="url(#logoGradient)"
      />
      <circle cx="12" cy="12" r="1" fill="url(#logoGradient)" />
      <circle cx="8" cy="12" r="1" fill="url(#logoGradient)" />
      <circle cx="16" cy="12" r="1" fill="url(#logoGradient)" />
    </SvgIcon>
  );
};

export default Logo; 