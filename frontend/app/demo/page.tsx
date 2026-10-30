import Link from "next/link";
import DemoExperience from "@/components/DemoExperience";
import Brand from "@/components/Brand";
export default function DemoPage() { return <main className="demo-page"><header className="demo-nav"><Brand/><span>● INTERACTIVE EXPERIENCE · BROWSER ONLY</span><Link href="/">Back to product ↗</Link></header><DemoExperience/></main>; }
