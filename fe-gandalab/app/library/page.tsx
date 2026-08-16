import { LibraryClient } from './library-client'
import { getResources } from '@/lib/resources'

export const metadata = {
    title: 'Library - GandaLab',
    description: 'Explore our collection of educational resources.',
}

export default async function LibraryPage() {
    const resources = await getResources()
    return <LibraryClient initialResources={resources} />
}

