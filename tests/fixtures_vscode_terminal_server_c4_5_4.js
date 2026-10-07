const { createTerminalControlServer } = require("../vscode-extension/terminal_control");

const vscode = {
    window: {
        createTerminal(options) {
            return {
                options,
                show() {},
                sendText() {},
                dispose() {}
            };
        }
    }
};

const control = createTerminalControlServer(vscode, { port: 0 });

control.start().then((address) => {
    console.log(JSON.stringify({ port: address.port }));
    console.log("READY");
}).catch((error) => {
    console.error(error);
    process.exit(1);
});

process.on("SIGTERM", async () => {
    await control.stop();
    process.exit(0);
});
