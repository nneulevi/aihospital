// orval.config.mjs
export default {
    'his-api': {
        input: { target: 'http://localhost:8092/v3/api-docs' },
        output: {
            mode: 'single',
            client: 'axios',
            target: './src/api/client.ts',
            schemas: './src/api/model',
            clean: true,
        },
    },
}