const vscode = require("vscode");
const path = require("path");
const pacepilot = require("../extension.js");

function waitForWorkspace(timeoutMs = 5000) {
    return new Promise((resolve, reject) => {
        if (vscode.workspace.workspaceFolders) {
            resolve();
            return;
        }

        const disposable = vscode.workspace.onDidChangeWorkspaceFolders(() => {
            if (vscode.workspace.workspaceFolders) {
                disposable.dispose();
                resolve();
            }
        });

        setTimeout(() => {
            disposable.dispose();
            reject(new Error("Workspace was not established by Extension Development Host"));
        }, timeoutMs);
    });
}

function waitForTerminalEvent(eventName, expectedName, timeoutMs = 5000) {
    return new Promise((resolve, reject) => {
        const disposable =
            eventName === "open"
                ? vscode.window.onDidOpenTerminal((terminal) => {
                    if (terminal.name === expectedName) {
                        disposable.dispose();
                        resolve();
                    }
                })
                : vscode.window.onDidCloseTerminal((terminal) => {
                    if (terminal.name === expectedName) {
                        disposable.dispose();
                        resolve();
                    }
                });

        setTimeout(() => {
            disposable.dispose();
            reject(
                new Error(
                    `onDid${eventName === "open" ? "Open" : "Close"}Terminal was not observed`
                )
            );
        }, timeoutMs);
    });
}

async function run() {
    if (!vscode.workspace.workspaceFolders) {
        const workspaceRoot = path.resolve(__dirname, "../..");

        const added = vscode.workspace.updateWorkspaceFolders(
            0,
            0,
            {
                uri: vscode.Uri.file(workspaceRoot),
                name: path.basename(workspaceRoot)
            }
        );

        if (!added) {
            throw new Error("Failed to establish Extension Development Host workspace");
        }

        await waitForWorkspace();
    }

    const context = {
        subscriptions: []
    };

    pacepilot.activate(context);

    const commands = await vscode.commands.getCommands(true);

    for (const command of [
        "pacepilot.createTask",
        "pacepilot.pause",
        "pacepilot.resume",
        "pacepilot.stop",
        "pacepilot.showStatus"
    ]) {
        if (!commands.includes(command)) {
            throw new Error(`Command not registered: ${command}`);
        }
    }

    const workspaceRoot =
        vscode.workspace.workspaceFolders[0].uri.fsPath;

    if (!workspaceRoot) {
        throw new Error("Workspace root was not resolved");
    }

    const terminalName = "PacePilot C2.2 Smoke";
    const opened = waitForTerminalEvent("open", terminalName);

    const terminal = vscode.window.createTerminal({
        name: terminalName
    });

    terminal.show(true);
    await opened;

    const terminalExists = vscode.window.terminals.some(
        (item) => item.name === terminalName
    );

    if (!terminalExists) {
        throw new Error("Terminal was not created");
    }

    const closed = waitForTerminalEvent("close", terminalName);

    terminal.dispose();
    await closed;

    await vscode.commands.executeCommand("pacepilot.showStatus");

    for (const disposable of context.subscriptions) {
        disposable.dispose();
    }

    console.log("PACEPILOT_C2_2_EXTENSION_HOST_PASS");
}

function activate(context) {
    context.subscriptions.push(
        vscode.commands.registerCommand(
            "pacepilot.c2_2_test",
            () => run()
        )
    );
}

module.exports = {
    activate,
    run
};


