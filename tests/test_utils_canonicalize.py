"""Unit tests for canonicalize_project_identifier() in utils.py."""

from __future__ import annotations

from mcp_agent_mail.utils import canonicalize_project_identifier


class TestCanonicalizeProjectIdentifier:
    """Test cases for path canonicalization utility."""

    # --- WSL path conversions ---

    def test_wsl_path_basic(self) -> None:
        """WSL /mnt/c/foo/bar should convert to c:/foo/bar."""
        assert canonicalize_project_identifier("/mnt/c/foo/bar") == "c:/foo/bar"

    def test_wsl_path_uppercase_drive(self) -> None:
        """WSL path with uppercase drive letter should lowercase."""
        assert canonicalize_project_identifier("/mnt/C/foo/bar") == "c:/foo/bar"

    def test_wsl_path_different_drive(self) -> None:
        """WSL path with different drive letters."""
        assert canonicalize_project_identifier("/mnt/d/WORKSPACES") == "d:/WORKSPACES"
        assert canonicalize_project_identifier("/mnt/E/projects/app") == "e:/projects/app"

    def test_wsl_root_drive(self) -> None:
        """WSL path to drive root."""
        assert canonicalize_project_identifier("/mnt/c/") == "c:/"
        assert canonicalize_project_identifier("/mnt/c") == "c:/"

    # --- Windows path conversions ---

    def test_windows_path_backslashes(self) -> None:
        """Windows path with backslashes should convert."""
        assert canonicalize_project_identifier("C:\\foo\\bar") == "c:/foo/bar"

    def test_windows_path_uppercase(self) -> None:
        """Windows path with uppercase drive should lowercase."""
        assert canonicalize_project_identifier("C:/foo/bar") == "c:/foo/bar"

    def test_windows_path_already_canonical(self) -> None:
        """Already canonical Windows path should pass through."""
        assert canonicalize_project_identifier("c:/foo/bar") == "c:/foo/bar"

    def test_windows_mixed_slashes(self) -> None:
        """Windows path with mixed slashes should normalize."""
        assert canonicalize_project_identifier("C:/foo\\bar") == "c:/foo/bar"
        assert canonicalize_project_identifier("c:\\foo/bar\\baz") == "c:/foo/bar/baz"

    def test_windows_root_drive(self) -> None:
        """Windows drive root paths."""
        assert canonicalize_project_identifier("C:\\") == "c:/"
        assert canonicalize_project_identifier("C:") == "c:/"
        assert canonicalize_project_identifier("d:/") == "d:/"

    def test_windows_no_leading_slash(self) -> None:
        """Windows path without leading slash after drive."""
        assert canonicalize_project_identifier("C:foo") == "c:/foo"
        assert canonicalize_project_identifier("D:bar\\baz") == "d:/bar/baz"

    # --- Linux path passthrough ---

    def test_linux_path_passthrough(self) -> None:
        """Linux absolute paths should pass through unchanged."""
        assert canonicalize_project_identifier("/home/user/project") == "/home/user/project"
        assert canonicalize_project_identifier("/var/lib/app") == "/var/lib/app"

    def test_linux_root(self) -> None:
        """Linux root path."""
        assert canonicalize_project_identifier("/") == "/"

    # --- Edge cases ---

    def test_empty_string(self) -> None:
        """Empty string should return empty string."""
        assert canonicalize_project_identifier("") == ""

    def test_whitespace_only(self) -> None:
        """Whitespace-only string should return empty string."""
        assert canonicalize_project_identifier("   ") == ""
        assert canonicalize_project_identifier("\t\n") == ""

    def test_whitespace_trimmed(self) -> None:
        """Leading/trailing whitespace should be trimmed."""
        assert canonicalize_project_identifier("  /mnt/c/foo  ") == "c:/foo"
        assert canonicalize_project_identifier("\tC:\\bar\n") == "c:/bar"

    def test_non_path_identifier_passthrough(self) -> None:
        """Non-path identifiers should pass through."""
        assert canonicalize_project_identifier("my-project") == "my-project"
        assert canonicalize_project_identifier("some_identifier") == "some_identifier"
        assert canonicalize_project_identifier("project-123") == "project-123"

    def test_repeated_slashes_collapsed(self) -> None:
        """Repeated slashes should be collapsed."""
        assert canonicalize_project_identifier("/mnt/c//foo//bar") == "c:/foo/bar"
        assert canonicalize_project_identifier("C:\\\\foo\\\\bar") == "c:/foo/bar"
        assert canonicalize_project_identifier("/home//user///project") == "/home/user/project"

    def test_trailing_slash_removed(self) -> None:
        """Trailing slashes should be removed (except for roots)."""
        assert canonicalize_project_identifier("/mnt/c/foo/") == "c:/foo"
        assert canonicalize_project_identifier("C:\\foo\\bar\\") == "c:/foo/bar"
        assert canonicalize_project_identifier("/home/user/project/") == "/home/user/project"

    # --- Equivalence tests (the core bug fix) ---

    def test_wsl_windows_equivalence(self) -> None:
        """Same physical path via WSL and Windows should produce same result."""
        wsl_path = "/mnt/c/WORKSPACES/project"
        windows_path = "C:\\WORKSPACES\\project"

        canonical_wsl = canonicalize_project_identifier(wsl_path)
        canonical_windows = canonicalize_project_identifier(windows_path)

        assert canonical_wsl == canonical_windows
        assert canonical_wsl == "c:/WORKSPACES/project"

    def test_various_formats_equivalence(self) -> None:
        """Various formats of same path should all canonicalize identically."""
        paths = [
            "/mnt/c/Users/Me/project",
            "C:\\Users\\Me\\project",
            "c:/Users/Me/project",
            "C:/Users\\Me/project",
            "  C:\\Users\\Me\\project  ",
        ]

        results = [canonicalize_project_identifier(p) for p in paths]
        assert all(r == results[0] for r in results)
        assert results[0] == "c:/Users/Me/project"


class TestCanonicalizeIntegrationWithSlugify:
    """Test that canonicalized paths produce consistent slugs."""

    def test_slugify_after_canonicalize(self) -> None:
        """Canonicalized paths should produce same slug."""
        from mcp_agent_mail.utils import slugify

        wsl_path = "/mnt/c/WORKSPACES/project"
        windows_path = "C:\\WORKSPACES\\project"

        canonical_wsl = canonicalize_project_identifier(wsl_path)
        canonical_windows = canonicalize_project_identifier(windows_path)

        slug_wsl = slugify(canonical_wsl)
        slug_windows = slugify(canonical_windows)

        assert slug_wsl == slug_windows
