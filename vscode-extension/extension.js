const vscode = require("vscode");
const { createTerminalControlServer } = require("./terminal_control");

const DEFAULT_ENDPOINT = "http://127.0.0.1:8765/agent";

let state = {
    workspaceRoot: null,
    activeTerminal: null,
    lastCommand: null,
    lastResponse: null,
    taskContext: {
        project_id: null,
        task_id: null,
        workflow_id: null
    }
};

let terminalControl = null;

function endpoint() {
    return vscode.workspace
        .getConfiguration("pacepilot")
        .get("endpoint", DEFAULT_ENDPOINT);
}

async function send(command, taskId, payload = "") {
    const response = await fetch(endpoint(), {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            command,
            task_id: taskId,
            payload,
            workflow_id: null,
            operations: []
        })
    });

    const result = await response.json();

    if (!response.ok || result.error) {
        throw new Error(result.error || `HTTP ${response.status}`);
    }

    state.lastCommand = command;
    state.lastResponse = result;
    state.taskContext = {
        project_id: null,
        task_id: result.task_id ?? taskId,
        workflow_id: result.workflow_id ?? null
    };
    return result;
}

function currentWorkspace() {
    return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? null;
}

async function createTask() {
    const taskId = await vscode.window.showInputBox({
        prompt: "PacePilot task ID",
        placeHolder: "task-001"
    });

    if (!taskId) {
        return;
    }

    const payload = await vscode.window.showInputBox({
        prompt: "PacePilot task payload",
        placeHolder: "Describe the task"
    });

    if (payload === undefined) {
        return;
    }

    try {
        const result = await send("create_task", taskId, payload);
        vscode.window.showInformationMessage(
            `PacePilot task created: ${result.task_id}`
        );
    } catch (error) {
        vscode.window.showErrorMessage(`PacePilot: ${error.message}`);
    }
}

async function runtimeCommand(command) {
    const taskId = state.lastResponse?.task_id;

    if (!taskId) {
        vscode.window.showWarningMessage(
            "PacePilot: no task is currently associated with this session."
        );
        return;
    }

    try {
        const result = await send(command, taskId, "");
        vscode.window.showInformationMessage(
            `PacePilot ${command}: ${result.value}`
        );
    } catch (error) {
        vscode.window.showErrorMessage(`PacePilot: ${error.message}`);
    }
}

function showStatus() {
    const workspace = state.workspaceRoot ?? "(none)";
    const terminal = state.activeTerminal
        ? state.activeTerminal.name
        : "(none)";
    const command = state.lastCommand ?? "(none)";

    vscode.window.showInformationMessage(
        `PacePilot | workspace=${workspace} | terminal=${terminal} | last=${command}`
    );
}

function activate(context) {
    const configuredTerminalPort = Number(
        vscode.workspace
            .getConfiguration("pacepilot")
            .get("terminalControlPort", 8766)
    );
    const terminalPort =
        Number.isInteger(configuredTerminalPort) && configuredTerminalPort > 0
            ? configuredTerminalPort
            : 8766;

    terminalControl = createTerminalControlServer(vscode, {
        port: terminalPort
    });

    terminalControl.start().catch((error) => {
        vscode.window.showErrorMessage(
            "PacePilot terminal control: " + error.message
        );
    });
    state.workspaceRoot = currentWorkspace();

    context.subscriptions.push(
        vscode.commands.registerCommand(
            "pacepilot.createTask",
            createTask
        ),
        vscode.commands.registerCommand(
            "pacepilot.pause",
            () => runtimeCommand("pause")
        ),
        vscode.commands.registerCommand(
            "pacepilot.resume",
            () => runtimeCommand("resume")
        ),
        vscode.commands.registerCommand(
            "pacepilot.stop",
            () => runtimeCommand("stop")
        ),
        vscode.commands.registerCommand(
            "pacepilot.showStatus",
            showStatus
        )
    );

    context.subscriptions.push(
        vscode.workspace.onDidChangeWorkspaceFolders(() => {
            state.workspaceRoot = currentWorkspace();
        }),
        vscode.window.onDidOpenTerminal((terminal) => {
            state.activeTerminal = terminal;
        }),
        vscode.window.onDidCloseTerminal((terminal) => {
            if (state.activeTerminal === terminal) {
                state.activeTerminal = null;
            }
        })
    );

    if (vscode.window.terminals.length > 0) {
        state.activeTerminal = vscode.window.activeTerminal ??
            vscode.window.terminals[0];
    }
}

async function deactivate() {
    const control = terminalControl;
    terminalControl = null;
    state.activeTerminal = null;

    if (control) {
        await control.stop();
    }
}

module.exports = {
    activate,
    deactivate
};
