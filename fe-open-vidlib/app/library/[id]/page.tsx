import { getResourceById } from "@/lib/resources"
import { notFound } from "next/navigation"
import { ResourcePageClient } from "./resource-page-client"

interface PageProps {
    params: Promise<{
        id: string
    }>
}

export default async function ResourcePage(props: PageProps) {
    const params = await props.params
    const resource = await getResourceById(decodeURIComponent(params.id))

    if (!resource) {
        notFound()
    }

    return <ResourcePageClient resource={resource} />
}

