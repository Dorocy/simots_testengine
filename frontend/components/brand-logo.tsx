import Image from 'next/image';
import logo from '@/lib/ezAAS_logo.svg';

interface BrandLogoProps {
  title?: string;
  className?: string;
  imageClassName?: string;
  titleClassName?: string;
}

export function BrandLogo({
  title = 'ezAAS',
  className = 'flex items-center gap-3',
  imageClassName = 'h-9 w-auto',
  titleClassName = 'text-xl font-bold tracking-tight',
}: BrandLogoProps) {
  return (
    <div className={className}>
      <Image
        src={logo}
        alt={`${title} 로고`}
        priority
        className={imageClassName}
      />
      <span className={titleClassName}>{title}</span>
    </div>
  );
}
