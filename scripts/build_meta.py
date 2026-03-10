import json
import os
import subprocess
from datetime import datetime


def main() -> None:
    prs = json.loads(os.environ.get("PRS_JSON", "[]"))
    merged = next((pr for pr in prs if pr.get("merged_at")), None)

    if merged:
        dt = datetime.fromisoformat(merged["merged_at"].replace("Z", "+00:00"))
        updated_date = dt.strftime("%d/%m/%Y")
        source = "last_merged_pr"
    else:
        updated_date = subprocess.check_output(
            [
                "git",
                "log",
                "-1",
                "--date=format:%d/%m/%Y",
                "--format=%ad",
                "origin/main",
            ],
            text=True,
        ).strip()
        source = "last_commit_main"

    with open("docs/assets/build-meta.json", "w", encoding="utf-8") as f:
        json.dump(
            {"updatedDate": updated_date, "source": source},
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"build-meta.json generado: {updated_date} ({source})")


if __name__ == "__main__":
    main()
