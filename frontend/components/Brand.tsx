import Image from "next/image";
import Link from "next/link";

type BrandProps = {
  className?: string;
};

export default function Brand({ className = "wordmark" }: BrandProps) {
  return (
    <Link className={`opsyro-brand ${className}`} href="/" aria-label="OPSYRO home">
      <Image className="opsyro-mark" src="/opsyro-symbol.svg" alt="" width={28} height={28} />
      <span>OPSYRO</span>
    </Link>
  );
}
