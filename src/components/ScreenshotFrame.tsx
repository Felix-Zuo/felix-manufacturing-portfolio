import Image from "next/image";

type ScreenshotFrameProps = {
  src: string;
  alt: string;
  url?: string;
  sizes?: string;
  eager?: boolean;
  className?: string;
};

export function ScreenshotFrame({ src, alt, url, sizes, eager = false, className }: ScreenshotFrameProps) {
  return (
    <figure className={`overflow-hidden rounded-md border hairline bg-[#0a101d] shadow-[0_24px_80px_-32px_rgba(2,6,17,0.9)] ${className ?? ""}`}>
      <div className="flex items-center gap-3 border-b hairline px-4 py-2.5">
        <span className="flex gap-1.5" aria-hidden="true">
          <span className="h-2.5 w-2.5 rounded-full bg-slate-700" />
          <span className="h-2.5 w-2.5 rounded-full bg-slate-700" />
          <span className="h-2.5 w-2.5 rounded-full bg-slate-700" />
        </span>
        {url && (
          <span className="min-w-0 truncate rounded border hairline bg-[#070c16] px-2.5 py-1 font-mono text-[11px] text-slate-500">
            {url.replace(/^https:\/\//, "")}
          </span>
        )}
      </div>
      <div className="relative aspect-[16/10] bg-[#070c16]">
        <Image
          src={src}
          alt={alt}
          fill
          sizes={sizes ?? "(max-width: 1024px) 100vw, 50vw"}
          className="object-cover object-top"
          loading={eager ? "eager" : "lazy"}
          fetchPriority={eager ? "high" : "auto"}
        />
      </div>
    </figure>
  );
}
