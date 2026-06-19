import * as vscode from "vscode";

interface ChatResponse {
  reply: string;
  session_id: string;
  agent: string;
}

function getConfig() {
  const config = vscode.workspace.getConfiguration("vidyaCopilot");
  return {
    serverUrl: config.get<string>("serverUrl", "http://127.0.0.1:8000"),
    apiKey: config.get<string>("apiKey", "dev-local-key"),
    defaultAgent: config.get<string>("defaultAgent", "coding"),
  };
}

async function callCopilot(
  message: string,
  agent?: string,
  sessionId?: string
): Promise<ChatResponse> {
  const { serverUrl, apiKey, defaultAgent } = getConfig();
  const response = await fetch(`${serverUrl}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
    },
    body: JSON.stringify({
      message,
      agent: agent || defaultAgent,
      session_id: sessionId,
    }),
  });
  if (!response.ok) {
    throw new Error(`Vidya Copilot error: ${response.status}`);
  }
  return response.json() as Promise<ChatResponse>;
}

export function activate(context: vscode.ExtensionContext) {
  let sessionId: string | undefined;

  const chatPanel = async () => {
    const input = await vscode.window.showInputBox({
      prompt: "Ask Vidya Copilot",
      placeHolder: "Create a Playwright framework with POM...",
    });
    if (!input) return;

    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "Vidya Copilot thinking..." },
      async () => {
        try {
          const result = await callCopilot(input, undefined, sessionId);
          sessionId = result.session_id;
          const doc = await vscode.workspace.openTextDocument({
            content: result.reply,
            language: "markdown",
          });
          await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
        } catch (err: unknown) {
          vscode.window.showErrorMessage(`Vidya Copilot: ${err}`);
        }
      }
    );
  };

  const askSelection = async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const selection = editor.document.getText(editor.selection);
    if (!selection) {
      vscode.window.showWarningMessage("Select code first.");
      return;
    }
    const question = await vscode.window.showInputBox({
      prompt: "What do you want to know about this code?",
    });
    if (!question) return;

    const message = `${question}\n\n\`\`\`\n${selection}\n\`\`\``;
    const result = await callCopilot(message, "coding", sessionId);
    sessionId = result.session_id;
    const doc = await vscode.workspace.openTextDocument({
      content: result.reply,
      language: "markdown",
    });
    await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
  };

  const indexProject = async () => {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) return;
    const { serverUrl, apiKey } = getConfig();
    const response = await fetch(`${serverUrl}/api/codebase/index`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
      body: JSON.stringify({ project_path: folder.uri.fsPath }),
    });
    const data = await response.json();
    vscode.window.showInformationMessage(
      `Indexed ${data.files_scanned || 0} files`
    );
  };

  const reviewFile = async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const content = editor.document.getText();
    const fileName = editor.document.fileName.split(/[/\\]/).pop();
    const message = `Review this file (${fileName}) and suggest improvements:\n\n\`\`\`\n${content.slice(0, 12000)}\n\`\`\``;
    const result = await callCopilot(message, "coding", sessionId);
    sessionId = result.session_id;
    const doc = await vscode.workspace.openTextDocument({
      content: result.reply,
      language: "markdown",
    });
    await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
  };

  context.subscriptions.push(
    vscode.commands.registerCommand("vidyaCopilot.openChat", chatPanel),
    vscode.commands.registerCommand("vidyaCopilot.askSelection", askSelection),
    vscode.commands.registerCommand("vidyaCopilot.indexProject", indexProject),
    vscode.commands.registerCommand("vidyaCopilot.reviewFile", reviewFile)
  );
}

export function deactivate() {}
