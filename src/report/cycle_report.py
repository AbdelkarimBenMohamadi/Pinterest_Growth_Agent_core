import json
import io
import logging
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)


class CycleReport:
    def __init__(self, cycle_start: datetime):
        self.cycle_start = cycle_start
        self.cycle_end: datetime | None = None
        self.keywords_found: int = 0
        self.trends_found: int = 0
        self.briefs_created: int = 0
        self.images_generated: int = 0
        self.pins_posted: int = 0
        self.pins_failed: int = 0
        self.scrape_errors: int = 0
        self.shadowban_detected: bool = False
        self.shadowban_check_passed: bool = False
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.new_keywords: list[str] = []
        self.top_keywords: list[dict[str, Any]] = []
        self.posted_pins: list[dict[str, Any]] = []
        self.engagement_summary: list[dict[str, Any]] = []
        self.research_details: dict[str, Any] = {}
        self.destination_link_mode: str = "none"
        self.destination_link: str = ""
        self.seo_scraper_health: dict[str, Any] = {}
        self.trend_scraper_health: dict[str, Any] = {}

    def finish(self) -> None:
        self.cycle_end = datetime.now(timezone.utc)

    def duration_seconds(self) -> float:
        if self.cycle_end and self.cycle_start:
            return (self.cycle_end - self.cycle_start).total_seconds()
        return 0.0

    def duration_str(self) -> str:
        secs = self.duration_seconds()
        if secs < 60:
            return f"{secs:.1f}s"
        mins = int(secs // 60)
        rem_secs = int(secs % 60)
        return f"{mins}m {rem_secs}s"

    def write_to_log(self, text: str) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self._log_file.write(f"[{timestamp}] {text}\n")

    def _write_file(self, filepath: Path, content: str) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")

    def print_summary(self) -> None:
        console = Console(force_terminal=True)
        console.print()
        console.print(Panel.fit(
            "[bold cyan]Pinterest Growth Agent - Cycle Report[/bold cyan]",
            style="bold cyan"
        ))

        status = "[green]SUCCESS[/green]" if self.pins_posted > 0 and not self.shadowban_detected else "[yellow]COMPLETED WITH WARNINGS[/yellow]"
        if self.shadowban_detected:
            status = "[red]SHADOWBAN DETECTED[/red]"

        meta_lines = [
            f"[dim]Started:[/dim]   {self.cycle_start.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"[dim]Duration:[/dim]  {self.duration_str()}",
            f"[dim]Status:[/dim]    {status}",
        ]
        console.print(Panel(
            "\n".join(meta_lines), title="[bold]Cycle Summary[/bold]", style="dim"
        ))
        console.print()

        self._print_research_tables(console)
        console.print()
        self._print_posting_table(console)
        console.print()
        self._print_engagement_table(console)
        console.print()
        self._print_health_table(console)
        console.print()
        self._print_errors_warnings(console)
        console.print()

    def _print_research_tables(self, console: Console) -> None:
        console.print("[bold]Research Phase[/bold]")

        if self.research_details:
            kw_table = Table(show_header=True, header_style="bold magenta", expand=False)
            kw_table.add_column("Keyword", style="cyan")
            kw_table.add_column("Rank", justify="right", style="green")
            kw_table.add_column("Source", style="dim")

            for kw in self.research_details.get("keywords", [])[:10]:
                kw_table.add_row(
                    kw.get("term") or "",
                    str(kw.get("suggestion_rank") or ""),
                    kw.get("source") or ""
                )
            console.print(kw_table)
            console.print(f"  [dim]> {self.keywords_found} total keywords found[/dim]")
        else:
            console.print(f"  [dim]> {self.keywords_found} keywords found[/dim]")

        console.print()

        if self.research_details.get("trends"):
            trend_table = Table(show_header=True, header_style="bold yellow", expand=False)
            trend_table.add_column("Trend", style="cyan")
            trend_table.add_column("Velocity", justify="right", style="yellow")
            trend_table.add_column("Category", style="dim")
            for t in self.research_details.get("trends", [])[:10]:
                trend_table.add_row(
                    t.get("name") or "",
                    f"{t.get('velocity') or 0:.2f}",
                    t.get("category") or ""
                )
            console.print(trend_table)
            console.print(f"  [dim]> {self.trends_found} total trends found[/dim]")

    def _print_posting_table(self, console: Console) -> None:
        console.print("[bold]Posting Phase[/bold]")

        pin_table = Table(show_header=True, header_style="bold green", expand=False)
        pin_table.add_column("#", justify="right", style="dim")
        pin_table.add_column("Keyword", style="cyan")
        pin_table.add_column("Title", style="white")
        pin_table.add_column("Board", style="dim")
        pin_table.add_column("Status", style="green")
        pin_table.add_column("URL", style="blue")

        for i, pin in enumerate(self.posted_pins, 1):
            status_color = "green" if pin.get("status") == "posted" else "red"
            url = pin.get("url") or "-"
            board = pin.get("board") or "-"
            pin_table.add_row(
                str(i),
                pin.get("keyword") or "",
                textwrap.shorten(pin.get("title") or "", width=40),
                textwrap.shorten(board, width=20),
                f"[{status_color}]{pin.get('status') or ''}[/{status_color}]",
                textwrap.shorten(url, width=35) if url != "-" else "-"
            )

        console.print(pin_table)

        summary = f"  Posted: {self.pins_posted}  |  Failed: {self.pins_failed}  |  Generated: {self.images_generated}"
        if self.destination_link_mode != "none" and self.destination_link:
            summary += f"  |  Link mode: {self.destination_link_mode}  ->  {self.destination_link}"
        console.print(f"  [dim]{summary}[/dim]")

    def _print_engagement_table(self, console: Console) -> None:
        console.print("[bold]Engagement (Last 7 Days)[/bold]")

        eng_table = Table(show_header=True, header_style="bold blue", expand=False)
        eng_table.add_column("Pin", style="cyan")
        eng_table.add_column("Keyword", style="dim")
        eng_table.add_column("Saves", justify="right", style="green")
        eng_table.add_column("Clicks", justify="right", style="yellow")
        eng_table.add_column("CTR %", justify="right", style="magenta")
        eng_table.add_column("Save Rate %", justify="right", style="cyan")

        total_saves = 0
        total_clicks = 0
        for e in self.engagement_summary:
            eng_table.add_row(
                str(e.get("pin_id") or ""),
                textwrap.shorten(e.get("keyword") or "", width=25),
                str(e.get("saves") or 0),
                str(e.get("clicks") or 0),
                f"{e.get('ctr') or 0:.1f}",
                f"{e.get('save_rate') or 0:.1f}",
            )
            total_saves += e.get("saves") or 0
            total_clicks += e.get("clicks") or 0

        console.print(eng_table)
        console.print(f"  [dim]Total - Saves: {total_saves}  |  Clicks: {total_clicks}[/dim]")

    def _print_health_table(self, console: Console) -> None:
        console.print("[bold]Scraper Health[/bold]")

        health_table = Table(show_header=True, header_style="bold red", expand=False)
        health_table.add_column("Module", style="cyan")
        health_table.add_column("Runs", justify="right", style="dim")
        health_table.add_column("Success", justify="right", style="green")
        health_table.add_column("Failed", justify="right", style="red")
        health_table.add_column("Avg Results", justify="right", style="yellow")
        health_table.add_column("Last Error", style="red")

        for health in [self.seo_scraper_health, self.trend_scraper_health]:
            if health:
                health_table.add_row(
                    health.get("module_name", ""),
                    str(health.get("run_count", 0)),
                    str(health.get("success_count", 0)),
                    str(health.get("failure_count", 0)),
                    f"{health.get('avg_results', 0):.1f}",
                    textwrap.shorten(health.get("last_error") or "-", width=30)
                )

        console.print(health_table)

    def _print_errors_warnings(self, console: Console) -> None:
        if self.warnings or self.errors:
            if self.warnings:
                console.print("[bold]Warnings[/bold]")
                for w in self.warnings:
                    console.print(f"  [yellow]~ {w}[/yellow]")
                console.print()

        if self.errors:
            console.print("[bold]Errors[/bold]")
            for e in self.errors:
                console.print(f"  [red]x {e}[/red]")
            console.print()

    def print_file_report(self) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        duration = self.duration_str()

        lines: list[str] = [
            "=" * 70,
            "PINTEREST GROWTH AGENT - DAILY CYCLE REPORT",
            "=" * 70,
            f"Generated:    {timestamp}",
            f"Started:      {self.cycle_start.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Duration:     {duration}",
            f"Status:       {'SUCCESS' if self.pins_posted > 0 and not self.shadowban_detected else 'COMPLETED WITH WARNINGS' if not self.shadowban_detected else 'SHADOWBAN DETECTED'}",
            "",
        ]

        lines.append("-" * 70)
        lines.append("RESEARCH PHASE")
        lines.append("-" * 70)
        lines.append(f"  Keywords found:  {self.keywords_found}")
        lines.append(f"  Trends found:   {self.trends_found}")
        if self.new_keywords:
            lines.append(f"  New keywords:   {', '.join(self.new_keywords[:10])}")

        if self.top_keywords:
            lines.append("  Top Keywords by Score:")
            for kw in self.top_keywords[:10]:
                lines.append(f"    - {kw['term']} (score: {kw['performance_score']:.2f}, rank: {kw['suggestion_rank']})")

        lines.append("")
        lines.append("-" * 70)
        lines.append("POSTING PHASE")
        lines.append("-" * 70)
        lines.append(f"  Content briefs created: {self.briefs_created}")
        lines.append(f"  Images generated:       {self.images_generated}")
        lines.append(f"  Pins posted:            {self.pins_posted}")
        lines.append(f"  Pins failed:            {self.pins_failed}")
        if self.destination_link_mode != "none" and self.destination_link:
            lines.append(f"  Destination link mode:  {self.destination_link_mode}")
            lines.append(f"  Destination link:      {self.destination_link}")

        lines.append("  Posted Pins:")
        for pin in self.posted_pins:
            lines.append(f"    [{pin.get('status', '').upper()}] {pin.get('title', '')}")
            if pin.get("url"):
                lines.append(f"      URL: {pin.get('url', '')}")
            lines.append(f"      Keyword: {pin.get('keyword', '')} | Board: {pin.get('board', 'N/A')}")

        lines.append("")
        lines.append("-" * 70)
        lines.append("ENGAGEMENT (LAST 7 DAYS)")
        lines.append("-" * 70)

        total_saves = 0
        total_clicks = 0
        for e in self.engagement_summary:
            lines.append(
                f"  Pin {e.get('pin_id')}: "
                f"Saves={e.get('saves', 0)}, Clicks={e.get('clicks', 0)}, "
                f"CTR={e.get('ctr', 0):.1f}%, Save Rate={e.get('save_rate', 0):.1f}%"
            )
            total_saves += e.get("saves", 0)
            total_clicks += e.get("clicks", 0)

        lines.append(f"  Totals - Saves: {total_saves}  |  Clicks: {total_clicks}")

        lines.append("")
        lines.append("-" * 70)
        lines.append("SCRAPER HEALTH")
        lines.append("-" * 70)

        for health in [self.seo_scraper_health, self.trend_scraper_health]:
            if health:
                lines.append(
                    f"  {health['module_name']}: "
                    f"runs={health['run_count']}, "
                    f"success={health['success_count']}, "
                    f"failed={health['failure_count']}, "
                    f"avg_results={health['avg_results']:.1f}"
                )
                if health.get("last_error"):
                    lines.append(f"    Last error: {health['last_error']}")

        lines.append("")
        lines.append("-" * 70)
        lines.append("SHADOWBAN CHECK")
        lines.append("-" * 70)
        lines.append(f"  Detected:     {'YES' if self.shadowban_detected else 'NO'}")
        lines.append(f"  Check passed: {'YES' if self.shadowban_check_passed else 'NO'}")

        if self.errors:
            lines.append("")
            lines.append("-" * 70)
            lines.append("ERRORS")
            lines.append("-" * 70)
            for e in self.errors:
                lines.append(f"  x {e}")

        if self.warnings:
            lines.append("")
            lines.append("-" * 70)
            lines.append("WARNINGS")
            lines.append("-" * 70)
            for w in self.warnings:
                lines.append(f"  ~ {w}")

        lines.append("")
        lines.append("=" * 70)
        lines.append(f"Report generated at {timestamp}")
        lines.append("=" * 70)

        content = "\n".join(lines)
        log_path = Path("data/cycle_reports") / f"cycle_{self.cycle_start.strftime('%Y%m%d_%H%M%S')}.log"
        self._write_file(log_path, content)

        latest_path = Path("data/cycle_report.log")
        latest_path.write_text(content, encoding="utf-8")
        logger.info(f"Cycle report saved to {log_path}")
