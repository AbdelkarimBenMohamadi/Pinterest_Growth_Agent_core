import typer
import asyncio
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.utils.config import load_config
from src.utils.logger import setup_logging
from src.store.database import Database
from src.orchestrator import retry_posting_pin, run_daily_cycle, start_scheduler

app = typer.Typer(help="Pinterest Growth Agent — AI-powered Pinterest automation.")
console = Console()
logger = logging.getLogger(__name__)

@app.callback()
def main():
    """Pinterest Growth Agent setup."""
    setup_logging()

@app.command()
def start(
    browser_mode: str = typer.Option("", "--browser-mode", help="Override browser mode: gui or headless"),
):
    """Start the APScheduler loop for daily Pinterest growth."""
    config = load_config()
    if browser_mode:
        _set_browser_mode(config, browser_mode)
    db = Database(config["paths"]["database"])
    db.initialize()
    console.print("[bold green]Starting APScheduler background loop...[/bold green]")
    start_scheduler(config)

@app.command()
def run_now(
    force: bool = typer.Option(False, "--force", help="Bypass daily safety limits and schedule waiting"),
    link: str = typer.Option("", "--link", help="Override default_destination_link for this run"),
    browser_mode: str = typer.Option("", "--browser-mode", help="Override browser mode: gui or headless"),
    schedule_mode: str = typer.Option("", "--schedule-mode", help="Override posting schedule mode: scheduled or immediate"),
    max_pins: int = typer.Option(0, "--max-pins", help="Maximum pins to process in this run; 0 means no override"),
):
    """Force a single daily cycle immediately."""
    config = load_config()
    if link:
        config.setdefault("posting", {})["default_destination_link"] = link
    if browser_mode:
        _set_browser_mode(config, browser_mode)
    if schedule_mode:
        _set_schedule_mode(config, schedule_mode)
    db = Database(config["paths"]["database"])
    db.initialize()
    console.print(f"[bold cyan]Starting manual daily cycle...[/bold cyan]")
    asyncio.run(run_daily_cycle(db, config, force=force, max_pins=max_pins or None))


@app.command()
def retry_post(
    pin_id: int = typer.Argument(..., help="Existing local pin ID to retry"),
    link: str = typer.Option("", "--link", help="Override default_destination_link for this retry"),
    browser_mode: str = typer.Option("", "--browser-mode", help="Override browser mode: gui or headless"),
):
    """Retry posting one existing generated pin without regenerating image or metadata."""
    config = load_config()
    if link:
        config.setdefault("posting", {})["default_destination_link"] = link
    if browser_mode:
        _set_browser_mode(config, browser_mode)
    db = Database(config["paths"]["database"])
    db.initialize()
    console.print(f"[bold cyan]Retrying post for pin {pin_id}...[/bold cyan]")
    result = asyncio.run(retry_posting_pin(db, config, pin_id))
    if result.status == "posted" and result.verified:
        console.print(f"[bold green]Verified Pinterest URL:[/bold green] {result.url}")
    elif result.status == "unverified":
        console.print(f"[bold yellow]Post unverified:[/bold yellow] {result.message}")
    else:
        console.print(f"[bold red]Post failed:[/bold red] {result.message}")

@app.command()
def stats():
    """Show a rich terminal dashboard of agent status and metrics."""
    config = load_config()
    db = Database(config["paths"]["database"])
    db.initialize()

    recent_pins = db.get_recent_pins(days=7)
    total_pins = len(recent_pins)
    posted = sum(1 for p in recent_pins if p.status == "posted")
    top_keywords = db.get_top_keywords(limit=10)

    conn = db._connect()
    try:
        cursor = conn.execute("SELECT COUNT(*) as count FROM keywords")
        kw_count = cursor.fetchone()[0]
        cursor2 = conn.execute("SELECT COUNT(*) as count FROM trends")
        trend_count = cursor2.fetchone()[0]
        cursor3 = conn.execute("SELECT action, created_at FROM agent_log ORDER BY created_at DESC LIMIT 5")
        recent_actions = cursor3.fetchall()
    finally:
        conn.close()

    # Create Summary Panel
    summary_text = (
        f"Pins Posted (7d): [bold blue]{posted}[/bold blue] / {total_pins}\n"
        f"Keywords in DB: [bold blue]{kw_count}[/bold blue]\n"
        f"Trends in DB: [bold blue]{trend_count}[/bold blue]"
    )
    console.print(Panel(summary_text, title="PGA Status Summary", expand=False))

    # Top Keywords Table
    if top_keywords:
        table = Table(title="Top Keywords")
        table.add_column("Keyword", style="cyan")
        table.add_column("Score", justify="right", style="green")
        
        for kw in top_keywords:
            table.add_row(kw.term, f"{kw.performance_score:.2f}")
        console.print(table)

    # Recent Actions
    if recent_actions:
        action_table = Table(title="Recent Actions")
        action_table.add_column("Time", style="dim")
        action_table.add_column("Action", style="magenta")
        for action_row in recent_actions:
            action_table.add_row(action_row[1], action_row[0])
        console.print(action_table)


def _set_browser_mode(config: dict, mode: str) -> None:
    if mode not in {"gui", "headless"}:
        raise typer.BadParameter("browser mode must be 'gui' or 'headless'")
    config.setdefault("browser", {})["mode"] = mode


def _set_schedule_mode(config: dict, mode: str) -> None:
    if mode not in {"scheduled", "immediate"}:
        raise typer.BadParameter("schedule mode must be 'scheduled' or 'immediate'")
    config.setdefault("posting", {})["schedule_mode"] = mode

if __name__ == "__main__":
    app()
