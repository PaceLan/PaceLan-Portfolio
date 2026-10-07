const assert = require("assert");
const http = require("http");
const {
    createTerminalControlServer
} = require("../vscode-extension/terminal_control");

function createMockVscode() {
    let nextTerminal = 1;

    return {
        window: {
            createTerminal(options) {
                const terminal = {
                    id: nextTerminal++,
                    options,
                    commands: [],
                    shown: false,
                    disposed: false,
                    show() {
                        this.shown = true;
                    },
                    sendText(command) {
                        this.commands.push(command);
                    },
                    dispose() {
                        this.disposed = true;
                    }
                };

                return terminal;
            }
        }
    };
}

function request(port, body) {
    return new Promise((resolve, reject) => {
        const payload = JSON.stringify(body);

        const request = http.request(
            {
                host: "127.0.0.1",
                port,
                path: "/terminal",
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Content-Length": Buffer.byteLength(payload)
                }
            },
            response => {
                let data = "";

                response.on("data", chunk => {
                    data += chunk;
                });

                response.on("end", () => {
                    resolve({
                        status: response.statusCode,
                        body: JSON.parse(data)
                    });
                });
            }
        );

        request.on("error", reject);
        request.write(payload);
        request.end();
    });
}

(async () => {
    const vscode = createMockVscode();

    const server = createTerminalControlServer(
        vscode,
        {
            host: "127.0.0.1",
            port: 0
        }
    );

    const address = await server.start();

    try {
        const port = address.port;

        const created = await request(port, {
            operation: "create",
            cwd: "C:\\workspace",
            name: "PacePilot",
            session_id: "session-1"
        });

        assert.strictEqual(created.status, 200);
        assert.strictEqual(created.body.session_id, "session-1");
        assert.ok(created.body.terminal_id);

        const terminalId = created.body.terminal_id;

        const statusBySession = await request(port, {
            operation: "status",
            session_id: "session-1"
        });

        assert.strictEqual(statusBySession.status, 200);
        assert.strictEqual(
            statusBySession.body.terminal_id,
            terminalId
        );
        assert.strictEqual(
            statusBySession.body.session_id,
            "session-1"
        );

        const sent = await request(port, {
            operation: "send",
            terminal_id: terminalId,
            session_id: "session-1",
            command: "echo hello"
        });

        assert.strictEqual(sent.status, 200);
        assert.strictEqual(
            sent.body.terminal_id,
            terminalId
        );
        assert.strictEqual(
            sent.body.session_id,
            "session-1"
        );

        const mismatch = await request(port, {
            operation: "status",
            terminal_id: terminalId,
            session_id: "session-2"
        });

        assert.strictEqual(mismatch.status, 400);
        assert.match(
            mismatch.body.error,
            /session_id does not match terminal/
        );

        const duplicate = await request(port, {
            operation: "create",
            cwd: "C:\\workspace",
            session_id: "session-1"
        });

        assert.strictEqual(duplicate.status, 400);
        assert.match(
            duplicate.body.error,
            /session_id already exists/
        );

        const closed = await request(port, {
            operation: "close",
            terminal_id: terminalId,
            session_id: "session-1"
        });

        assert.strictEqual(closed.status, 200);
        assert.strictEqual(
            closed.body.terminal_id,
            terminalId
        );
        assert.strictEqual(
            closed.body.session_id,
            "session-1"
        );
        assert.strictEqual(
            closed.body.state,
            "CLOSED"
        );
    } finally {
        await server.stop();
    }

    console.log("C4.5.5 terminal session binding: PASS");
})().catch(error => {
    console.error(error);
    process.exit(1);
});
