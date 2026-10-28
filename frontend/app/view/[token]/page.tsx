import ViewerPreview from "@/components/ViewerPreview";
export default function ViewerPage({ params }: { params: { token: string } }) { return <ViewerPreview token={params.token}/>; }
