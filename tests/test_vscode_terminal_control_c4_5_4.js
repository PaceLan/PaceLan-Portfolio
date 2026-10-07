const assert = require("assert");
const http = require("http");
const { createTerminalControlServer } =
    require("../vscode-extension/terminal_control");

const created = [];

const vscode = {
    window: {
        createTerminal(options) {
            const terminal = {
                options,
                sent: [],
                shown: false,
                disposed: false,
                show() {
                    this.shown = true;
                },
                sendText(command, addNewLine) {
                    this.sent.push({ command, addNewLine });
                },
                dispose() {
                    this.disposed = true;
                }
            };
            created.push(terminal);
            return terminal;
        }
    }
};

function request(port, body) {
    return new Promise((resolve, reject) => {
        const payload = JSON.stringify(body);

        const req = http.request(
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

        req.on("error", reject);
        req.end(payload);
    });
}

(async () => {
    const control = createTerminalControlServer(vscode, {
        port: 0
    });

    const address = await control.start();
    const port = address.port;

    try {
        let result = await request(port, {
            operation: "create",
            cwd: "C:\\work",
            name: "PacePilot"
        });

        assert.strictEqual(result.status, 200);
        assert.strictEqual(result.body.state, "RUNNING");
        assert.strictEqual(created.length, 1);
        assert.strictEqual(created[0].options.cwd, "C:\\work");
        assert.strictEqual(created[0].shown, true);

        const terminalId = result.body.terminal_id;

        result = await request(port, {
            operation: "send",
            terminal_id: terminalId,
            command: "python -m unittest"
        });

        assert.strictEqual(result.body.state, "RUNNING");
        assert.deepStrictEqual(created[0].sent[0], {
            command: "python -m unittest",
            addNewLine: true
        });

        result = await request(port, {
            operation: "status",
            terminal_id: terminalId
        });

        assert.strictEqual(result.body.state, "RUNNING");

        result = await request(port, {
            operation: "close",
            terminal_id: terminalId
        });

        assert.strictEqual(result.body.state, "CLOSED");
        assert.strictEqual(created[0].disposed, true);
    } finally {
        await control.stop();
    }

    console.log("C4.5.4 terminal control: PASS");
})().catch(error => {
    console.error(error);
    process.exit(1);
});
