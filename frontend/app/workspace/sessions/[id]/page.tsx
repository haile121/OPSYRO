import SessionInsights from "@/components/SessionInsights";
export default function SessionPage({ params }: { params: { id: string } }) { return <SessionInsights id={params.id}/>; }
