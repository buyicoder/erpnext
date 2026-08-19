const { get_conf } = require("../node_utils");
const conf = get_conf();

function get_url(socket, path) {
	if (!path) {
		path = "";
	}
	let url = socket.request.headers.origin;
	const hostname = url ? new URL(url).hostname : "";
	if (["localhost", "127.0.0.1"].includes(hostname)) {
		url = process.env.FRAPPE_INTERNAL_BACKEND_URL || "http://backend:8000";
	} else if (conf.developer_mode) {
		let [protocol, host] = url.split(":");
		url = `${protocol}:${host}:${conf.webserver_port}`;
	}
	return url + path;
}

module.exports = {
	get_url,
};
