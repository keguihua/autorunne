from awf.core.scanner import recommend_next_action, scan_repo


def test_scan_repo_detects_node_stack(node_repo):
    scan = scan_repo(node_repo)
    assert "node" in scan["stack"]
    assert "react" in scan["framework"]
    assert scan["package_manager"] == ["npm"]
    assert scan["commands"]["test"] == "npm test"


def test_scan_repo_detects_python_stack(python_repo):
    scan = scan_repo(python_repo)
    assert "python" in scan["stack"]
    assert "fastapi" in scan["framework"]
    assert scan["commands"]["test"] == "pytest"


def test_scan_repo_detects_nextjs_and_pnpm(next_pnpm_repo):
    scan = scan_repo(next_pnpm_repo)
    assert scan["package_manager"] == ["pnpm"]
    assert "nextjs" in scan["framework"]
    assert scan["commands"]["run"] == "pnpm run dev"
    assert scan["commands"]["build"] == "pnpm run build"


def test_scan_repo_detects_go_projects(go_repo):
    scan = scan_repo(go_repo)
    assert scan["stack"] == ["go"]
    assert scan["framework"] == ["go"]
    assert scan["commands"]["run"] == "go run ."
    assert scan["commands"]["test"] == "go test ./..."


def test_scan_repo_detects_rust_projects(rust_repo):
    scan = scan_repo(rust_repo)
    assert scan["stack"] == ["rust"]
    assert scan["framework"] == ["rust"]
    assert scan["commands"]["run"] == "cargo run"


def test_scan_repo_detects_c_projects(c_repo):
    scan = scan_repo(c_repo)
    assert scan["stack"] == ["c"]
    assert "cmake" in scan["framework"]
    assert scan["commands"]["build"] == "cmake -S . -B build && cmake --build build"


def test_scan_repo_detects_cpp_projects(cpp_repo):
    scan = scan_repo(cpp_repo)
    assert scan["stack"] == ["cpp"]
    assert "cmake" in scan["framework"]
    assert scan["commands"]["build"] == "cmake -S . -B build && cmake --build build"


def test_scan_repo_detects_monorepo_workspace(monorepo_repo):
    scan = scan_repo(monorepo_repo)
    assert "node" in scan["stack"]
    assert "monorepo" in scan["framework"]
    assert "turborepo" in scan["framework"]
    assert scan["package_manager"] == ["pnpm"]
    assert "apps" in scan["source_dirs"]
    assert "packages" in scan["source_dirs"]


def test_recommend_next_action_uses_readme_signal(git_repo):
    scan = scan_repo(git_repo)
    assert recommend_next_action(scan).startswith("Create or improve the project README")
