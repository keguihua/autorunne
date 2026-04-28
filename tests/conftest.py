from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    return repo


@pytest.fixture()
def node_repo(git_repo: Path) -> Path:
    (git_repo / "package.json").write_text(
        '{"name":"demo","scripts":{"test":"vitest","dev":"vite"},"dependencies":{"react":"18.0.0","vite":"5.0.0"}}',
        encoding="utf-8",
    )
    (git_repo / "src").mkdir()
    (git_repo / "src" / "index.js").write_text("console.log('hi')\n", encoding="utf-8")
    return git_repo


@pytest.fixture()
def next_pnpm_repo(git_repo: Path) -> Path:
    (git_repo / "package.json").write_text(
        '{"name":"next-demo","scripts":{"test":"vitest","dev":"next dev","build":"next build"},"dependencies":{"next":"15.0.0","react":"19.0.0"}}',
        encoding="utf-8",
    )
    (git_repo / "pnpm-lock.yaml").write_text("lockfile\n", encoding="utf-8")
    (git_repo / "app").mkdir()
    (git_repo / "app" / "page.tsx").write_text("export default function Page(){return null}\n", encoding="utf-8")
    return git_repo


@pytest.fixture()
def go_repo(git_repo: Path) -> Path:
    (git_repo / "go.mod").write_text("module example.com/demo\n\ngo 1.22\n", encoding="utf-8")
    (git_repo / "main.go").write_text("package main\nfunc main(){}\n", encoding="utf-8")
    return git_repo


@pytest.fixture()
def monorepo_repo(git_repo: Path) -> Path:
    (git_repo / "package.json").write_text(
        '{"name":"mono-demo","private":true,"workspaces":["apps/*","packages/*"],"scripts":{"test":"turbo test","dev":"turbo dev","build":"turbo build"},"devDependencies":{"turbo":"2.0.0"}}',
        encoding="utf-8",
    )
    (git_repo / "pnpm-workspace.yaml").write_text("packages:\n  - apps/*\n  - packages/*\n", encoding="utf-8")
    (git_repo / "turbo.json").write_text('{"pipeline":{}}\n', encoding="utf-8")
    (git_repo / "apps").mkdir()
    (git_repo / "packages").mkdir()
    return git_repo


@pytest.fixture()
def haopay_style_monorepo(git_repo: Path) -> Path:
    """Multi-package repo with no root package.json, matching a real haopay-style layout."""
    (git_repo / "frontend").mkdir()
    (git_repo / "frontend" / "package.json").write_text(
        '{"name":"haopay-frontend","scripts":{"dev":"vite","build":"tsc && vite build","preview":"vite preview"},"dependencies":{"@vitejs/plugin-react":"latest"},"devDependencies":{"vite":"^5.0.0","typescript":"^5.0.0"}}',
        encoding="utf-8",
    )
    (git_repo / "backend").mkdir()
    (git_repo / "backend" / "package.json").write_text(
        '{"name":"haopay-backend","scripts":{"start":"node server.js","dev":"nodemon --legacy-watch --watch server.js --watch routes --watch models --watch utils --watch middleware server.js","worker:indexer":"node workers/indexerWorker.js","worker:webhooks":"node workers/webhookWorker.js","worker:once":"node workers/runWorkersOnce.js","test":"node --test tests/**/*.test.js","test:apiKey":"node --test tests/apiKeyHardening.test.js"},"dependencies":{"express":"^4.18.0"},"devDependencies":{"nodemon":"^3.0.0"}}',
        encoding="utf-8",
    )
    (git_repo / "backend" / "server.js").write_text("import express from 'express'\n", encoding="utf-8")
    (git_repo / "contracts").mkdir()
    (git_repo / "contracts" / "package.json").write_text(
        '{"name":"haopay-contracts","scripts":{"test":"npx hardhat test","compile":"npx hardhat compile","deploy:testnet":"npx hardhat run scripts/deployTestnet.js --network arbitrumSepolia","deploy:all":"npx hardhat run scripts/deployAll.js","deploy:testnet:single":"npx hardhat run scripts/deployTestnet.js --network arbitrumSepolia","deploy:testnet:all":"npx hardhat run scripts/deployTestnetAll.js","plan:set":"npx hardhat run scripts/setMerchantPlan.js --network arbitrumSepolia","plan:read":"npx hardhat run scripts/readMerchantPricing.js --network arbitrumSepolia"},"devDependencies":{"hardhat":"^2.22.0"}}',
        encoding="utf-8",
    )
    return git_repo


@pytest.fixture()
def rust_repo(git_repo: Path) -> Path:
    (git_repo / "Cargo.toml").write_text(
        "[package]\nname='demo'\nversion='0.1.0'\nedition='2021'\n",
        encoding="utf-8",
    )
    (git_repo / "src").mkdir()
    (git_repo / "src" / "main.rs").write_text("fn main() {}\n", encoding="utf-8")
    return git_repo


@pytest.fixture()
def c_repo(git_repo: Path) -> Path:
    (git_repo / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.20)\nproject(demo_c C)\nadd_executable(demo main.c)\n",
        encoding="utf-8",
    )
    (git_repo / "main.c").write_text("int main(void){return 0;}\n", encoding="utf-8")
    return git_repo


@pytest.fixture()
def cpp_repo(git_repo: Path) -> Path:
    (git_repo / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.20)\nproject(demo_cpp CXX)\nadd_executable(demo main.cpp)\n",
        encoding="utf-8",
    )
    (git_repo / "main.cpp").write_text("int main(){return 0;}\n", encoding="utf-8")
    return git_repo


@pytest.fixture()
def python_repo(git_repo: Path) -> Path:
    (git_repo / "pyproject.toml").write_text(
        "[project]\nname='demo'\ndependencies=['fastapi']\n",
        encoding="utf-8",
    )
    (git_repo / "src").mkdir()
    (git_repo / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
    (git_repo / "tests").mkdir()
    (git_repo / "tests" / "test_basic.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return git_repo


@pytest.fixture()
def standard_library_python_repo(git_repo: Path) -> Path:
    (git_repo / "README.md").write_text(
        "# course demo\n\n```bash\npython -m pytest -q\npython app.py\n```\n",
        encoding="utf-8",
    )
    (git_repo / "app.py").write_text(
        "from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer\n\n"
        "class Handler(BaseHTTPRequestHandler):\n    pass\n\n"
        "def run():\n    ThreadingHTTPServer(('127.0.0.1', 8010), Handler).serve_forever()\n\n"
        "if __name__ == '__main__':\n    run()\n",
        encoding="utf-8",
    )
    (git_repo / "store.py").write_text("class Store:\n    pass\n", encoding="utf-8")
    (git_repo / "tests").mkdir()
    (git_repo / "tests" / "test_store.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return git_repo
