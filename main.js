const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow;
let analyzeWindow;

// 1. Desktop 위치의 output 폴더 생성/반환
function getOutputDir() {
  // 사용자의 바탕화면 경로
  const desktopPath = app.getPath('desktop');
  const outputDir = path.join(desktopPath, 'output');

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
    console.log(`Created output directory at: ${outputDir}`);
  }
  return outputDir;
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    }
  });

  mainWindow.loadFile('main.html');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createAnalyzeWindow() {
  analyzeWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    }
  });

  analyzeWindow.loadFile('analyze.html');
  analyzeWindow.webContents.openDevTools();

  analyzeWindow.on('closed', () => {
    analyzeWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });

  // 앱 시작 시 한 번만 output 폴더 생성
  getOutputDir();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// HEX 색상을 RGB로 변환
function hexToRgb(hex) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return m ? { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) } : null;
}

// 2. 비디오 저장 핸들러
ipcMain.handle('save-video', async (event, buffer) => {
  try {
    const outputDir = getOutputDir();
    const outputPath = path.join(outputDir, 'input_video.mp4');

    const uint8Array = new Uint8Array(buffer);
    fs.writeFileSync(outputPath, Buffer.from(uint8Array));
    return { success: true };
  } catch (err) {
    console.error('save-video error:', err);
    return { success: false, error: err.message };
  }
});

// 3. 분석 시작 핸들러
ipcMain.handle('start-analysis', async (event, { videoPath, team1Color, team2Color }) => {
  try {
    const outputDir = getOutputDir();
    const team1Rgb = hexToRgb(team1Color);
    const team2Rgb = hexToRgb(team2Color);
    if (!team1Rgb || !team2Rgb) throw new Error('Invalid team colors');

    createAnalyzeWindow();

    // Python args: main.py 대신 패키징 시 .py 파일이 있는 위치 경로로 바꿀 것
    const script = path.join(__dirname, 'main.py');
    const pythonArgs = [
      script,
      videoPath,
      '--team1-color', team1Rgb.r, team1Rgb.g, team1Rgb.b,
      '--team2-color', team2Rgb.r, team2Rgb.g, team2Rgb.b
    ].map(String);

    const py = spawn('python3', pythonArgs);
    console.log('Spawned Python:', pythonArgs.join(' '));

    // (비디오 정보 조회, 데이터 수신 등 기존 로직 그대로)

    // 예시: 분석 완료 시 tracked_video.mp4가 outputDir에 생성되었다고 가정
    py.on('close', code => {
      analyzeWindow.webContents.send('analysis-complete', code === 0);
    });

    return { success: true };
  } catch (err) {
    console.error('start-analysis error:', err);
    return { success: false, error: err.message };
  }
});

// 4. 다운로드 핸들러 (비디오 & JSON)
ipcMain.handle('download-video', async (event, relativePath) => {
  try {
    const outputDir = getOutputDir();
    const sourcePath = path.join(outputDir, relativePath);
    const { canceled, filePath } = await dialog.showSaveDialog({
      title: 'Save Video',
      defaultPath: 'tracked_video.mp4',
      filters: [{ name: 'Videos', extensions: ['mp4'] }]
    });
    if (canceled) return { success: false };

    fs.copyFileSync(sourcePath, filePath);
    return { success: true };
  } catch (err) {
    console.error('download-video error:', err);
    return { success: false, error: err.message };
  }
});

ipcMain.handle('download-json', async (event, relativePath) => {
  try {
    const outputDir = getOutputDir();
    const sourcePath = path.join(outputDir, relativePath);
    const { canceled, filePath } = await dialog.showSaveDialog({
      title: 'Save JSON',
      defaultPath: 'tracking_data.json',
      filters: [{ name: 'JSON', extensions: ['json'] }]
    });
    if (canceled) return { success: false };

    fs.copyFileSync(sourcePath, filePath);
    return { success: true };
  } catch (err) {
    console.error('download-json error:', err);
    return { success: false, error: err.message };
  }
});

// 5. 파일 존재 여부 확인 핸들러
ipcMain.handle('check-video-file', async () => {
  const outputDir = getOutputDir();
  const videoPath = path.join(outputDir, 'tracked_video.mp4');
  return { exists: fs.existsSync(videoPath) };
});
