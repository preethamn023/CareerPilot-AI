#!/usr/bin/env node
/**
 * CareerPilot AI - development orchestrator.
 *
 * Runs the full stack in one process tree:
 *   - FastAPI backend  -> http://127.0.0.1:8000  (backend/.venv)
 *   - Vite frontend    -> http://0.0.0.0:3000    (proxies /api to the backend)
 *
 * The AI bridge (mini-services/ai-bridge) is started separately by
 * .zscripts/dev.sh as a mini-service on port 8010.
 */
const { spawn, spawnSync } = require("child_process")
const fs = require("fs")
const path = require("path")

const ROOT = path.resolve(__dirname, "..")
const logStream = fs.createWriteStream(path.join(ROOT, "dev.log"), { flags: "a" })

function log(message) {
  const line = `[${new Date().toISOString()}] [dev] ${message}`
  console.log(line)
  logStream.write(line + "\n")
}

function pipe(child, name) {
  const write = (chunk, target) => {
    const text = chunk.toString()
    process[target].write(`[${name}] ${text}`)
    logStream.write(`[${name}] ${text}`)
  }
  child.stdout.on("data", (d) => write(d, "stdout"))
  child.stderr.on("data", (d) => write(d, "stderr"))
  child.on("exit", (code) => log(`${name} exited with code ${code}`))
}

function runSync(cmd, args, cwd) {
  log(`$ ${cmd} ${args.join(" ")} (in ${path.relative(ROOT, cwd) || "."})`)
  const result = spawnSync(cmd, args, { cwd, stdio: "pipe", encoding: "utf8" })
  if (result.stdout) logStream.write(`[install] ${result.stdout}`)
  if (result.stderr) logStream.write(`[install] ${result.stderr}`)
  if (result.status !== 0) {
    throw new Error(`${cmd} ${args.join(" ")} failed with code ${result.status}`)
  }
}

function ensureFrontend() {
  const frontendDir = path.join(ROOT, "frontend")
  if (!fs.existsSync(path.join(frontendDir, "node_modules"))) {
    log("frontend/node_modules missing - installing dependencies...")
    runSync("bun", ["install"], frontendDir)
  }
}

function ensureBackend() {
  const backendDir = path.join(ROOT, "backend")
  const venvPython = path.join(backendDir, ".venv", "bin", "python")
  if (!fs.existsSync(venvPython)) {
    log("backend/.venv missing - creating virtual environment...")
    runSync("python3", ["-m", "venv", ".venv"], backendDir)
    runSync(venvPython, ["-m", "pip", "install", "--upgrade", "pip"], backendDir)
    runSync(venvPython, ["-m", "pip", "install", "-r", "requirements.txt"], backendDir)
  }
  return venvPython
}

const children = []

function shutdown() {
  log("shutting down child processes...")
  for (const child of children) {
    try {
      child.kill("SIGTERM")
    } catch {
      /* already gone */
    }
  }
  process.exit(0)
}

process.on("SIGINT", shutdown)
process.on("SIGTERM", shutdown)

try {
  ensureFrontend()
  const backendPython = ensureBackend()

  // Backend: FastAPI / uvicorn on 8000.
  const backend = spawn(
    backendPython,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    { cwd: path.join(ROOT, "backend") },
  )
  pipe(backend, "backend")
  children.push(backend)
  log("backend (uvicorn) starting on http://127.0.0.1:8000")

  // Frontend: Vite dev server on 3000 (proxies /api -> 8000).
  const frontend = spawn("bun", ["run", "dev"], { cwd: path.join(ROOT, "frontend") })
  pipe(frontend, "frontend")
  children.push(frontend)
  log("frontend (vite) starting on http://0.0.0.0:3000")

  log("CareerPilot AI dev stack is up. Frontend: http://localhost:3000 | API: http://localhost:8000/api/health")
} catch (error) {
  log(`startup failed: ${error && error.message ? error.message : error}`)
  shutdown()
}
