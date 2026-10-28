declare module 'react-gtm-module' {
    interface TagManagerArgs {
        gtmId: string
        auth?: string
        preview?: string
        dataLayer?: Record<string, unknown>
        dataLayerName?: string
        events?: Record<string, unknown>
    }

    interface DataLayerArgs {
        dataLayer?: Record<string, unknown>
        dataLayerName?: string
    }

    interface EventArgs {
        dataLayer?: Record<string, unknown>
        event?: string
    }

    const TagManager: {
        initialize(options: TagManagerArgs): void
        dataLayer(options: DataLayerArgs): void
        dataLayerEvent(options: EventArgs): void
    }

    export default TagManager
}

