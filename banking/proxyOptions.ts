import { readFileSync } from 'node:fs';
import type { IncomingMessage } from 'node:http';

export default function createProxyOptions() {
	const { webserver_port } = JSON.parse(
		readFileSync(new URL('../../../sites/common_site_config.json', import.meta.url), 'utf8')
	) as { webserver_port: string | number };

	return {
		'^/(app|api|assets|files|private)': {
			target: `http://127.0.0.1:${webserver_port}`,
			ws: true,
			router: function (req: IncomingMessage) {
				const site_name = req.headers?.host?.split(':')[0];
				return `http://${site_name ?? 'localhost'}:${webserver_port}`;
			}
		}
	};
}
