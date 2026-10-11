const http = require("http");

function createTerminalControlServer(vscode, options = {}) {
    const host = options.host ?? "127.0.0.1";
    const port = options.port ?? 8766;
    const terminals = new Map();
    const sessions = new Map();
    const closed = new Set();
    const closedResults = new Map();
    const executions = new Map();
    const pendingEnds = new WeakMap();
    const pendingStarts = new WeakMap();
    const subscriptions = [];
    const shellEventsAvailable =
        typeof vscode.window.onDidStartTerminalShellExecution === "function" &&
        typeof vscode.window.onDidEndTerminalShellExecution === "function";
    let nextId = 1;
    let nextCommandId = 1;
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
                terminal: record.terminal,
                record
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
                terminal: record.terminal,
                record
            };
        }

        return null;
    }

    function commandFields(record, commandId) {
        const command = commandId
            ? record.commands.get(commandId)
            : record.latestCommandId
                ? record.commands.get(record.latestCommandId)
                : null;

        return {
            command_id: command ? command.command_id : null,
            command_status: command ? command.command_status : "UNKNOWN",
            exit_code: command ? command.exit_code : null,
            output: command ? command.output : "",
            output_status: command ? command.output_status : "UNKNOWN"
        };
    }

    function closedCommandFields(snapshot, commandId) {
        if (!snapshot) {
            return {
                command_id: null,
                command_status: "UNKNOWN",
                exit_code: null,
                output: "",
                output_status: "UNKNOWN"
            };
        }

        const command = commandId
            ? snapshot.commands?.[commandId]
            : snapshot.latest;

        return command ? { ...command } : {
            command_id: null,
            command_status: "UNKNOWN",
            exit_code: null,
            output: "",
            output_status: "UNKNOWN"
        };
    }
    function applyExecutionEnd(event) {
        const matched = executions.get(event.execution);
        if (!matched) {
            pendingEnds.set(event.execution, event);
            return;
        }

        executions.delete(event.execution);

        const record = terminals.get(matched.terminalId);
        const command =
            record?.commands.get(matched.commandId) ??
            closedResults.get(matched.terminalId)
                ?.commands?.[matched.commandId];
        if (!command) return;

        const code = event.exitCode;
        command.exit_code = Number.isInteger(code) ? code : null;
        command.command_status =
            command.exit_code === 0 ? "SUCCEEDED" :
            command.exit_code !== null ? "FAILED" : "UNKNOWN";
    }

    if (shellEventsAvailable) {
        subscriptions.push(
            vscode.window.onDidStartTerminalShellExecution(event => {
                const terminalId = idFor(event.terminal);
                const record = terminalId
                    ? terminals.get(terminalId)
                    : null;
                if (!record) return;

                const matched = executions.get(event.execution);
                if (!matched) {
                    pendingStarts.set(event.execution, terminalId);
                    return;
                }
                if (matched.terminalId !== terminalId) return;

                const command = record.commands.get(matched.commandId);
                if (!command) return;

                command.command_status = "RUNNING";
            })
        );

        subscriptions.push(
            vscode.window.onDidEndTerminalShellExecution(
                event => applyExecutionEnd(event)
            )
        );
    }

    function waitForShellIntegration(terminal, timeoutMs = 10000) {
        if (typeof terminal.shellIntegration?.executeCommand === "function") {
            return Promise.resolve(terminal.shellIntegration);
        }
        if (typeof vscode.window.onDidChangeTerminalShellIntegration !== "function") {
            return Promise.reject(new Error(
                "Shell Integration events unavailable; command was not dispatched"
            ));
        }
        return new Promise((resolve, reject) => {
            let settled = false;
            let timer;
            let subscription;
            const finish = (error, integration) => {
                if (settled) return;
                settled = true;
                if (timer) clearTimeout(timer);
                subscription?.dispose();
                if (error) reject(error);
                else resolve(integration);
            };
            subscription = vscode.window.onDidChangeTerminalShellIntegration(event => {
                if (event.terminal === terminal &&
                    typeof event.terminal.shellIntegration?.executeCommand === "function") {
                    finish(null, event.terminal.shellIntegration);
                }
            });
            timer = setTimeout(() => finish(new Error(
                "Timed out waiting for Shell Integration; command was not dispatched"
            )), timeoutMs);
            if (typeof terminal.shellIntegration?.executeCommand === "function") {
                finish(null, terminal.shellIntegration);
            }
        });
    }

    async function handle(body) {
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
                session_id: sessionId,
                commands: new Map(),
                latestCommandId: null
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

            const terminalState = "RUNNING";
            const terminalRecord = record.record;

            if (!shellEventsAvailable) {
                throw new Error(
                    "Shell execution events unavailable; command was not dispatched"
                );
            }

            const shellIntegration = await waitForShellIntegration(record.terminal);
            const commandId = `command-${nextCommandId++}`;
            const command = {
                command_id: commandId,
                command: body.command ?? "",
                command_status: "DISPATCHED",
                exit_code: null,
                output: "",
                output_status: "PENDING"
            };

            terminalRecord.commands.set(commandId, command);
            terminalRecord.latestCommandId = commandId;

            try {
                const execution = shellIntegration.executeCommand(
                    body.command ?? ""
                );
                if (!execution || (
                    typeof execution !== "object" &&
                    typeof execution !== "function"
                )) {
                    throw new Error(
                        "Shell Integration returned no execution identity"
                    );
                }

                executions.set(execution, {
                    terminalId: record.terminal_id,
                    commandId
                });

                if (typeof execution.read !== "function") {
                    command.output_status = "UNAVAILABLE";
                } else {
                    (async () => {
                        try {
                            for await (const chunk of execution.read()) {
                                if (typeof chunk !== "string") {
                                    command.output_status = "ERROR";
                                    return;
                                }
                                command.output += chunk;
                            }
                            command.output_status = "CAPTURED";
                        } catch (_) {
                            command.output_status = "ERROR";
                        }
                    })();
                }

                if (pendingStarts.get(execution) === record.terminal_id) {
                    pendingStarts.delete(execution);
                    command.command_status = "RUNNING";
                }

                const pendingEnd = pendingEnds.get(execution);
                if (pendingEnd) {
                    pendingEnds.delete(execution);
                    applyExecutionEnd(pendingEnd);
                }
            } catch (error) {
                command.command_status = "FAILED";
                throw error;
            }

            return {
                operation,
                terminal_id: record.terminal_id,
                session_id: record.session_id,
                state: terminalState,
                ...commandFields(terminalRecord, commandId)
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
                        state: "CLOSED",
                        ...closedCommandFields(closedResults.get(body.terminal_id))
                    };
                }

                throw new Error("terminal not found");
            }

            for (const command of record.record.commands.values()) {
                if (
                    command.command_status === "DISPATCHED" ||
                    command.command_status === "RUNNING"
                ) {
                    command.command_status = "UNKNOWN";
                    command.exit_code = null;
                }
            }

            closedResults.set(
                record.terminal_id,
                {
                    session_id: record.session_id,
                    latest: record.record.latestCommandId
                        ? record.record.commands.get(record.record.latestCommandId)
                        : null,
                    commands: Object.fromEntries(
                        [...record.record.commands.entries()].map(
                            ([id, command]) => [id, command]
                        )
                    )
                }
            );

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
                state: "CLOSED",
                ...closedCommandFields(closedResults.get(record.terminal_id))
            };
        }

        if (operation === "status") {
            const record = resolveTerminal(body);

            if (record) {
                return {
                    operation,
                    terminal_id: record.terminal_id,
                    session_id: record.session_id,
                    state: "RUNNING",
                    ...commandFields(
                        record.record,
                        body.command_id
                    )
                };
            }

            if (
                body.terminal_id &&
                closed.has(body.terminal_id)
            ) {
                return {
                    operation,
                    terminal_id: body.terminal_id,
                    session_id: body.session_id ??
                        closedResults.get(body.terminal_id)?.session_id ?? null,
                    state: "CLOSED",
                    ...closedCommandFields(closedResults.get(body.terminal_id), body.command_id)
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

            request.on("end", async () => {
                try {
                    const body = JSON.parse(data || "{}");
                    const result = await handle(body);
                    json(response, 200, result);
                } catch (error) {
                    if (!response.headersSent) {
                        json(response, 400, { error: error.message });
                    }
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
        closedResults.clear();
        executions.clear();

        for (const subscription of subscriptions.splice(0)) {
            subscription?.dispose?.();
        }

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
