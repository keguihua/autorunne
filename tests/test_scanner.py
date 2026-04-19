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


def test_recommend_next_action_uses_readme_signal(git_repo):
    scan = scan_repo(git_repo)
    assert recommend_next_action(scan).startswith("Create or improve the project README")
