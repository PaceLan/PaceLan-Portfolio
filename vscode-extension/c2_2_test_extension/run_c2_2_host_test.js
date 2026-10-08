const path = require("path");
const { runTests } = require("@vscode/test-electron");

async function main() {
    const root = path.resolve(__dirname, "../..");
    const extensionDevelopmentPath = path.resolve(__dirname, "..");
    const extensionTestsPath = path.resolve(__dirname, "extension.js");
    const workspaceRoot = root;

    await runTests({
        extensionDevelopmentPath,
        extensionTestsPath,
        launchArgs: [workspaceRoot]
    });
}

main().catch((error) => {
    console.error(error);
    process.exit(1);
});

