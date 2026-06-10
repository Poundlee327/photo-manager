const { app, BrowserWindow, shell } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const net = require("net");

let mainWindow;
let backendProcess;

const BACKEND_PORT = 8000;
const FRONTEND_URL = app.isPackaged
  ? `file://${path.join(__dirname, "../frontend/dist/index.html")}`
  : "http://localhost:3000";

function startBackend() {
  const backendDir = app.isPackaged
    ? path.join(process.resourcesPath, "backend")
    : path.join(__dirname, "../backend");

  const python = process.platform === "win32" ? "python" : "python3";
  backendProcess = spawn(
    python,
    ["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)],
    { cwd: backendDir, stdio: "pipe" }
  );

  backendProcess.stdout.on("data", (d) => console.log("[backend]", d.toString()));
  backendProcess.stderr.on("data", (d) => console.error("[backend]", d.toString()));
}

function waitForBackend(callback, retries = 30) {
  const sock = net.createConnection({ port: BACKEND_PORT, host: "127.0.0.1" });
  sock.on("connect", () => { sock.destroy(); callback(); });
  sock.on("error", () => {
    if (retries > 0) setTimeout(() => waitForBackend(callback, retries - 1), 500);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: "hiddenInset",
    backgroundColor: "#1a1a2e",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadURL(FRONTEND_URL);

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

app.whenReady().then(() => {
  startBackend();
  waitForBackend(createWindow);

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (backendProcess) backendProcess.kill();
});
