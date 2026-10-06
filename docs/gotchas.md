# Gotchas (Windows dev setup)

- **Encoding:** Windows PowerShell 5.1 `Set-Content -Encoding utf8` writes a BOM, which breaks TOML and justfiles. Use the editor tools or `[IO.File]::WriteAllText(path, text, (New-Object Text.UTF8Encoding $false))`.
- **justfile is PowerShell.** The justfile sets `pwsh` as the shell on Linux, so PR checks run on `ubuntu-latest` (half the minutes). Pushes to `main` run on `windows-latest`. `-pre-commit install` is non-fatal on purpose.
- **Deny rules beat allow rules.** Never deny `.env.*`: it blocks `.env.example`. List specific env files.
- **pnpm 11+** blocks dependency build scripts: approve them in `pnpm-workspace.yaml` (`allowBuilds`).
- **ruff** needs `src = [...]` set if code lives in a subfolder, or imports get mis-sorted.
- **`gh repo edit`** needs `owner/repo`.
- **Verify before claiming done:** run `just setup; just lint; just test` from a clean copy in a real terminal.
