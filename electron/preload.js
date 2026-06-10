const { contextBridge } = require("electron");

// Expose minimal safe APIs to renderer if needed in future
contextBridge.exposeInMainWorld("electronAPI", {
  platform: process.platform,
});
