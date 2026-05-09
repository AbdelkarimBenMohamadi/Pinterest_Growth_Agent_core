import typer
import asyncio
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.utils.config import load_config
from src.utils.logger import setup_logging
from src.store.database import Database
from src.orchestrator import run_daily_cycle, start_scheduler
from src.facebook_orchestrator import run_facebook_daily_cycle
from src.instagram_orchestrator import run_instagram_daily_cycle
from src.twitter_orchestrator import run_twitter_daily_cycle

app = typer.Typer(help="Pinterest, Facebook, Instagram & Twitter Growth Agent — AI-powered automation.")
console = Console()
logger = logging.getLogger(__name__)

@app.callback()
def main():
    """Pinterest Growth Agent setup."""
    setup_logging()

@app.command()
def start():
    """Start the APScheduler loop for daily Pinterest growth."""
    config = load_config()
    db = Database(config["paths"]["database"])
    db.initialize()
    console.print("[bold green]Starting APScheduler background loop...[/bold green]")
    start_scheduler(config)

@app.command()
def run_now(
    force: bool = typer.Option(False, "--force", help="Bypass daily safety limits"),
    link: str = typer.Option("", "--link", help="Override default_destination_link for this run"),
):
    """Force a single daily Pinterest cycle immediately."""
    config = load_config()
    if link:
        config.setdefault("posting", {})["default_destination_link"] = link
    db = Database(config["paths"]["database"])
    db.initialize()
    console.print(f"[bold cyan]Starting manual Pinterest daily cycle...[/bold cyan]")
    asyncio.run(run_daily_cycle(db, config, force=force))

@app.command()
def fb_run_now(
    force: bool = typer.Option(False, "--force", help="Bypass daily safety limits"),
):
    """Force a single daily Facebook cycle immediately."""
    config = load_config()
    db = Database(config["paths"]["database"])
    db.initialize()
    console.print(f"[bold blue]Starting manual Facebook daily cycle...[/bold blue]")
    asyncio.run(run_facebook_daily_cycle(db, config, force=force))

@app.command()
def insta_run_now(
    force: bool = typer.Option(False, "--force", help="Bypass daily safety limits"),
):
    """Force a single daily Instagram cycle immediately."""
    config = load_config()
    db = Database(config["paths"]["database"])
    db.initialize()
    console.print(f"[bold magenta]Starting manual Instagram daily cycle...[/bold magenta]")
    asyncio.run(run_instagram_daily_cycle(db, config, force=force))

@app.command()
def twitter_run_now(
    force: bool = typer.Option(False, "--force", help="Bypass daily safety limits"),
):
    """Force a single daily Twitter cycle immediately."""
    config = load_config()
    db = Database(config["paths"]["database"])
    db.initialize()
    console.print(f"[bold white]Starting manual Twitter daily cycle...[/bold white]")
    asyncio.run(run_twitter_daily_cycle(db, config, force=force))

@app.command()
def stats():
    """Show a rich terminal dashboard of agent status and metrics."""
    config = load_config()
    db = Database(config["paths"]["database"])
    db.initialize()

    recent_pins = db.get_recent_pins(days=7)
    total_pins = len(recent_pins)
    posted = sum(1 for p in recent_pins if p.status == "posted")

    recent_fb = db.get_recent_facebook_posts(days=7)
    total_fb = len(recent_fb)
    posted_fb = sum(1 for p in recent_fb if p["status"] == "posted")

    recent_insta = db.get_recent_instagram_posts(days=7)
    total_insta = len(recent_insta)
    posted_insta = sum(1 for p in recent_insta if p["status"] == "posted")

    recent_twitter = db.get_recent_twitter_posts(days=7)
    total_twitter = len(recent_twitter)
    posted_twitter = sum(1 for p in recent_twitter if p["status"] == "posted")

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
        f"Facebook Posts (7d): [bold blue]{posted_fb}[/bold blue] / {total_fb}\n"
        f"Instagram Posts (7d): [bold blue]{posted_insta}[/bold blue] / {total_insta}\n"
        f"Twitter Posts (7d): [bold blue]{posted_twitter}[/bold blue] / {total_twitter}\n"
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

if __name__ == "__main__":
    app()