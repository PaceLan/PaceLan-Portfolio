const assert = require("assert");
const http = require("http");
const {
    createTerminalControlServer
} = require("../vscode-extension/terminal_control");

function createMockVscode() {
    const starts = [];
    const ends = [];
    const terminals = [];

    const window = {
        createTerminal(options) {
            const terminal = {
                options,
                executions: [],
                nextRead: null,
                nextEnd: null,
                disposed: false,
                show() {},
                dispose() {
                    this.disposed = true;
                }
            };
            terminal.shellIntegration = {
                executeCommand(commandLine) {
                    const read = terminal.nextRead;
                    terminal.nextRead = null;
                    const execution = {
                        commandLine: { value: commandLine }
                    };
                    if (read) execution.read = read;
                    terminal.executions.push(execution);
                    // Simulate VS Code firing the start event synchronously.
                    starts.forEach(callback => callback({ terminal, execution }));
                    if (terminal.nextEnd !== null) {
                        const end = terminal.nextEnd;
                        terminal.nextEnd = null;
                        ends.forEach(callback =>
                            callback({ terminal, execution, exitCode: end.exitCode })
                        );
                    }
                    return execution;
                }
            };
            terminals.push(terminal);
            return terminal;
        },
        onDidStartTerminalShellExecution(callback) {
            starts.push(callback);
            return { dispose() {} };
        },
        onDidEndTerminalShellExecution(callback) {
            ends.push(callback);
            return { dispose() {} };
        }
    };

    return {
        vscode: { window },
        terminals,
        emitStart(terminal, execution) {
            starts.forEach(callback =>
                callback({ terminal, execution })
            );
        },
        emitEnd(execution, exitCode) {
            ends.forEach(callback =>
                callback({ execution, exitCode })
            );
        }
    };
}

function request(port, body) {
    return new Promise((resolve, reject) => {
        const payload = JSON.stringify(body);
        const req = http.request({
            host: "127.0.0.1",
            port,
            path: "/terminal",
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Content-Length": Buffer.byteLength(payload)
            }
        }, response => {
            let data = "";
            response.on("data", chunk => data += chunk);
            response.on("end", () => {
                resolve({
                    status: response.statusCode,
                    body: JSON.parse(data)
                });
            });
        });
        req.on("error", reject);
        req.end(payload);
    });
}

async function main() {
    const mock = createMockVscode();
    const server = createTerminalControlServer(
        mock.vscode,
        { host: "127.0.0.1", port: 0 }
    );
    const address = await server.start();

    try {
        const created = await request(address.port, {
            operation: "create",
            cwd: "C:\\workspace",
            session_id: "c456-session"
        });
        assert.strictEqual(created.status, 200);

        const terminalId = created.body.terminal_id;
        const terminal = mock.terminals[0];

        async function sendAndStart(name) {
            const sent = await request(address.port, {
                operation: "send",
                terminal_id: terminalId,
                command: name
            });
            assert.strictEqual(sent.status, 200);
            assert.strictEqual(
                sent.body.command_status, "RUNNING"
            );
            assert.ok(sent.body.command_id);

            const execution =
                terminal.executions[terminal.executions.length - 1];
            assert.ok(execution, "executeCommand returned no execution");

            const immediate = await request(address.port, {
                operation: "status",
                terminal_id: terminalId,
                command_id: sent.body.command_id
            });
            assert.strictEqual(
                immediate.body.command_status, "RUNNING",
                "synchronous start event was lost"
            );
            mock.emitStart(terminal, execution);

            return { commandId: sent.body.command_id, execution };
        }

        // End event fires synchronously before executeCommand returns.
        terminal.nextEnd = { exitCode: 0 };
        const earlyEnd = await request(address.port, {
            operation: "send",
            terminal_id: terminalId,
            command: "synchronous-end"
        });
        assert.strictEqual(earlyEnd.status, 200);
        const earlyResult = await request(address.port, {
            operation: "status",
            terminal_id: terminalId,
            command_id: earlyEnd.body.command_id
        });
        assert.strictEqual(earlyResult.body.command_status, "SUCCEEDED");
        assert.strictEqual(earlyResult.body.exit_code, 0);

        // 1. 成功：退出码 0
        const success = await sendAndStart("success");
        mock.emitEnd(success.execution, 0);
        let result = await request(address.port, {
            operation: "status",
            terminal_id: terminalId,
            command_id: success.commandId
        });
        assert.strictEqual(result.body.command_status, "SUCCEEDED");
        assert.strictEqual(result.body.exit_code, 0);
        assert.strictEqual(result.body.command_id, success.commandId);

        // Duplicate/conflicting end events must not overwrite a confirmed result.
        mock.emitEnd(success.execution, 7);
        result = await request(address.port, {
            operation: "status",
            terminal_id: terminalId,
            command_id: success.commandId
        });
        assert.strictEqual(result.body.command_status, "SUCCEEDED");
        assert.strictEqual(result.body.exit_code, 0);

        // 2. 失败：非零退出码
        const missingCommand = await request(address.port, {
            operation: "status",
            terminal_id: terminalId,
            command_id: "command-does-not-exist"
        });
        assert.strictEqual(missingCommand.status, 200);
        assert.strictEqual(missingCommand.body.command_id, null);
        assert.strictEqual(missingCommand.body.command_status, "UNKNOWN");
        assert.strictEqual(missingCommand.body.exit_code, null);

        const failure = await sendAndStart("failure");
        mock.emitEnd(failure.execution, 7);
        result = await request(address.port, {
            operation: "status",
            terminal_id: terminalId,
            command_id: failure.commandId
        });
        assert.strictEqual(result.body.command_status, "FAILED");
        assert.strictEqual(result.body.exit_code, 7);
        assert.strictEqual(result.body.command_id, failure.commandId);

        // 3. 未知：事件没有提供有效退出码
        const unknown = await sendAndStart("unknown");
        mock.emitEnd(unknown.execution, undefined);
        result = await request(address.port, {
            operation: "status",
            terminal_id: terminalId,
            command_id: unknown.commandId
        });
        assert.strictEqual(result.body.command_status, "UNKNOWN");
        assert.strictEqual(result.body.exit_code, null);
        assert.strictEqual(result.body.command_id, unknown.commandId);

        // Output capture contract: chunks, empty output and read failures.
        async function waitForOutput(commandId, expected) {
            for (let i = 0; i < 50; i++) {
                const response = await request(address.port, {
                    operation: "status",
                    terminal_id: terminalId,
                    command_id: commandId
                });
                if (response.body.output_status === expected) {
                    return response.body;
                }
                await new Promise(resolve => setTimeout(resolve, 0));
            }
            throw new Error("output status did not reach " + expected);
        }

        terminal.nextRead = async function* () {
            yield "first ";
            yield "second";
        };
        let outputCase = await sendAndStart("output-captured");
        result = await waitForOutput(outputCase.commandId, "CAPTURED");
        assert.strictEqual(result.output, "first second");

        terminal.nextRead = async function* () {};
        outputCase = await sendAndStart("output-empty");
        result = await waitForOutput(outputCase.commandId, "CAPTURED");
        assert.strictEqual(result.output, "");

        outputCase = await sendAndStart("output-unavailable");
        result = await waitForOutput(outputCase.commandId, "UNAVAILABLE");
        assert.strictEqual(result.output, "");

        terminal.nextRead = async function* () {
            throw new Error("simulated read failure");
        };
        outputCase = await sendAndStart("output-error");
        await waitForOutput(outputCase.commandId, "ERROR");

        terminal.nextRead = async function* () {
            yield 42;
        };
        outputCase = await sendAndStart("output-invalid-chunk");
        await waitForOutput(outputCase.commandId, "ERROR");

        console.log("C6.5.11 OUTPUT CAPTURE TESTS: PASS");

        // 4. 终端关闭：仍在运行的命令不得伪报成功

        // Identical command text must retain distinct execution identities.
        const duplicateIds = [];
        const duplicateExecutions = [];
        for (let i = 0; i < 2; i++) {
            const sent = await request(address.port, {
                operation: "send",
                terminal_id: terminalId,
                command: "duplicate-command"
            });
            assert.strictEqual(sent.status, 200);
            duplicateIds.push(sent.body.command_id);
            duplicateExecutions.push(
                terminal.executions[terminal.executions.length - 1]
            );
        }
        assert.notStrictEqual(duplicateIds[0], duplicateIds[1]);
        assert.notStrictEqual(duplicateExecutions[0], duplicateExecutions[1]);

        mock.emitStart(terminal, duplicateExecutions[1]);
        mock.emitStart(terminal, duplicateExecutions[0]);

        for (const commandId of duplicateIds) {
            result = await request(address.port, {
                operation: "status",
                terminal_id: terminalId,
                command_id: commandId
            });
            assert.strictEqual(result.body.command_status, "RUNNING");
            assert.strictEqual(result.body.exit_code, null);
        }

        mock.emitEnd(duplicateExecutions[0], 0);
        mock.emitEnd(duplicateExecutions[1], 7);

        result = await request(address.port, {
            operation: "status",
            terminal_id: terminalId,
            command_id: duplicateIds[0]
        });
        assert.strictEqual(result.body.command_status, "SUCCEEDED");
        assert.strictEqual(result.body.exit_code, 0);

        result = await request(address.port, {
            operation: "status",
            terminal_id: terminalId,
            command_id: duplicateIds[1]
        });
        assert.strictEqual(result.body.command_status, "FAILED");
        assert.strictEqual(result.body.exit_code, 7);

        let releaseRead;
        terminal.nextRead = async function* () {
            await new Promise(resolve => { releaseRead = resolve; });
            yield "late output";
        };
        const pending = await sendAndStart("close-pending-output");
        for (let i = 0; i < 10 && !releaseRead; i++) {
            await new Promise(resolve => setTimeout(resolve, 0));
        }
        assert.strictEqual(typeof releaseRead, "function");

        let releaseErrorRead;
        terminal.nextRead = async function* () {
            await new Promise(resolve => { releaseErrorRead = resolve; });
            throw new Error("late read failure after close");
        };
        const pendingError = await sendAndStart("close-pending-output-error");
        for (let i = 0; i < 10 && !releaseErrorRead; i++) {
            await new Promise(resolve => setTimeout(resolve, 0));
        }
        assert.strictEqual(typeof releaseErrorRead, "function");

        const closed = await request(address.port, {
            operation: "close",
            terminal_id: terminalId
        });
        assert.strictEqual(closed.status, 200);
        assert.strictEqual(closed.body.state, "CLOSED");
        assert.strictEqual(terminal.disposed, true);

        // End event arrives after the terminal has closed.
        mock.emitEnd(pending.execution, 0);
        mock.emitEnd(pendingError.execution, 0);

        releaseRead();
        releaseErrorRead();

        result = await waitForOutput(pendingError.commandId, "ERROR");
        assert.strictEqual(result.state, "CLOSED");
        assert.strictEqual(result.command_id, pendingError.commandId);
        assert.strictEqual(result.command_status, "SUCCEEDED");
        assert.strictEqual(result.exit_code, 0);

        result = await waitForOutput(pending.commandId, "CAPTURED");
        assert.strictEqual(result.state, "CLOSED");
        assert.strictEqual(result.command_id, pending.commandId);
        assert.strictEqual(result.command_status, "SUCCEEDED");
        assert.strictEqual(result.exit_code, 0);
        assert.strictEqual(result.output, "late output");

        // Historical command status after close
        result = await request(address.port, {
            operation: "status",
            terminal_id: terminalId,
            command_id: success.commandId
        });
        assert.strictEqual(result.body.state, "CLOSED");
        assert.strictEqual(result.body.command_id, success.commandId);
        assert.strictEqual(result.body.command_status, "SUCCEEDED");
        assert.strictEqual(result.body.exit_code, 0);
        console.log("C4.5.6 JS EVENT TESTS: PASS");
        console.log("success: SUCCEEDED / exit_code=0");
        console.log("failure: FAILED / exit_code=7");
        console.log("unknown: UNKNOWN / exit_code=null");
        console.log("close: CLOSED / UNKNOWN / exit_code=null");
    } finally {
        await server.stop();
    }
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
