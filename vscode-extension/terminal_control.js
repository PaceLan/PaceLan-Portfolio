const http = require("http");

function createTerminalControlServer(vscode, options = {}) {
    const host = options.host ?? "127.0.0.1";
    const port = options.port ?? 8766;
    const terminals = new Map();
    const sessions = new Map();
    const closed = new Set();
    let nextId = 1;
    let server = null;

    function idFor(terminal) {
        for (const [id, record] of terminals) {
            if (record.terminal === terminal) {
                return id;
            }
        }
        return null;
    }

    function json(response, status, value) {
        const body = JSON.stringify(value);

        response.writeHead(status, {
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(body)
        });

        response.end(body);
    }

    function resolveTerminal(body) {
        if (body.terminal_id) {
            const record = terminals.get(body.terminal_id);

            if (!record) {
                return null;
            }

            if (
                body.session_id &&
                record.session_id !== body.session_id
            ) {
                throw new Error("session_id does not match terminal");
            }

            return {
                terminal_id: body.terminal_id,
                session_id: record.session_id,
                terminal: record.terminal
            };
        }

        if (body.session_id) {
            const terminalId = sessions.get(body.session_id);

            if (!terminalId) {
                return null;
            }

            const record = terminals.get(terminalId);

            if (!record) {
                return null;
            }

            return {
                terminal_id: terminalId,
                session_id: record.session_id,
                terminal: record.terminal
            };
        }

        return null;
    }

    function handle(body) {
        const operation = body.operation;

        if (operation === "create") {
            if (
                body.session_id &&
                sessions.has(body.session_id)
            ) {
                throw new Error("session_id already exists");
            }

            const terminal = vscode.window.createTerminal({
                name: body.name || "PacePilot",
                cwd: body.cwd
            });

            const terminalId = `terminal-${nextId++}`;
            const sessionId = body.session_id ?? null;

            terminals.set(terminalId, {
                terminal,
                session_id: sessionId
            });

            if (sessionId) {
                sessions.set(sessionId, terminalId);
            }

            terminal.show(true);

            return {
                operation,
                terminal_id: terminalId,
                session_id: sessionId,
                state: "RUNNING"
            };
        }

        if (operation === "send") {
            const record = resolveTerminal(body);

            if (!record) {
                throw new Error("terminal not found");
            }

            record.terminal.sendText(body.command ?? "", true);

            return {
                operation,
                terminal_id: record.terminal_id,
                session_id: record.session_id,
                state: "RUNNING"
            };
        }

        if (operation === "close") {
            const record = resolveTerminal(body);

            if (!record) {
                if (
                    body.terminal_id &&
                    closed.has(body.terminal_id)
                ) {
                    return {
                        operation,
                        terminal_id: body.terminal_id,
                        session_id: body.session_id ?? null,
                        state: "CLOSED"
                    };
                }

                throw new Error("terminal not found");
            }

            record.terminal.dispose();
            terminals.delete(record.terminal_id);

            if (record.session_id) {
                sessions.delete(record.session_id);
            }

            closed.add(record.terminal_id);

            return {
                operation,
                terminal_id: record.terminal_id,
                session_id: record.session_id,
                state: "CLOSED"
            };
        }

        if (operation === "status") {
            const record = resolveTerminal(body);

            if (record) {
                return {
                    operation,
                    terminal_id: record.terminal_id,
                    session_id: record.session_id,
                    state: "RUNNING"
                };
            }

            if (
                body.terminal_id &&
                closed.has(body.terminal_id)
            ) {
                return {
                    operation,
                    terminal_id: body.terminal_id,
                    session_id: body.session_id ?? null,
                    state: "CLOSED"
                };
            }

            throw new Error("terminal not found");
        }

        throw new Error(
            `unsupported terminal operation: ${operation}`
        );
    }

    async function start() {
        server = http.createServer((request, response) => {
            if (
                request.method !== "POST" ||
                request.url !== "/terminal"
            ) {
                json(response, 404, {
                    error: "not found"
                });
                return;
            }

            let data = "";

            request.on("data", chunk => {
                data += chunk;
            });

            request.on("end", () => {
                try {
                    const body = JSON.parse(data || "{}");
                    json(response, 200, handle(body));
                } catch (error) {
                    json(response, 400, {
                        error: error.message
                    });
                }
            });
        });

        await new Promise((resolve, reject) => {
            server.once("error", reject);
            server.listen(port, host, resolve);
        });

        return server.address();
    }

    async function stop() {
        for (const record of terminals.values()) {
            record.terminal.dispose();
        }

        terminals.clear();
        sessions.clear();

        if (!server) {
            return;
        }

        await new Promise(resolve => server.close(resolve));
        server = null;
    }

    return {
        start,
        stop,
        idFor
    };
}

module.exports = {
    createTerminalControlServer
};
