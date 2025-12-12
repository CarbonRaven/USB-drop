"""USB Drop CLI - Command line interface."""

import sys
from pathlib import Path
from typing import Optional

import click
import questionary
from rich.console import Console
from rich.table import Table

from . import __version__
from .api_client import APIClient, APIError, client
from .config import config
from .file_writer import (
    download_and_extract,
    find_usb_drives,
    list_usb_contents,
    verify_usb_contents,
)

console = Console()


def require_config(func):
    """Decorator to require CLI configuration."""

    def wrapper(*args, **kwargs):
        if not config.is_configured():
            console.print(
                "[red]CLI not configured. Run 'usb-drop config set-api <url>' and "
                "'usb-drop config set-key <key>' first.[/red]"
            )
            sys.exit(1)
        return func(*args, **kwargs)

    return wrapper


@click.group()
@click.version_option(version=__version__)
def cli():
    """USB Drop Campaign Manager CLI.

    Prepare and deploy USB drives for penetration testing campaigns.
    """
    pass


# Configuration commands
@cli.group()
def config_cmd():
    """Manage CLI configuration."""
    pass


@config_cmd.command("set-api")
@click.argument("url")
def set_api(url: str):
    """Set the API server URL."""
    config.api_url = url.rstrip("/")
    console.print(f"[green]API URL set to: {config.api_url}[/green]")


@config_cmd.command("set-key")
@click.argument("key")
def set_key(key: str):
    """Set the API key for authentication."""
    config.api_key = key
    console.print("[green]API key saved.[/green]")


@config_cmd.command("set-campaign")
@click.argument("campaign_id")
def set_default_campaign(campaign_id: str):
    """Set the default campaign ID."""
    config.default_campaign = campaign_id
    console.print(f"[green]Default campaign set to: {campaign_id}[/green]")


@config_cmd.command("show")
def show_config():
    """Show current configuration."""
    cfg = config.show()
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    for key, value in cfg.items():
        table.add_row(key, str(value) if value else "[dim]not set[/dim]")

    console.print(table)


# Renamed group to avoid conflict
cli.add_command(config_cmd, name="config")


# Campaign commands
@cli.command("list-campaigns")
@require_config
def list_campaigns():
    """List all campaigns."""
    try:
        campaigns = client.list_campaigns()

        if not campaigns:
            console.print("[yellow]No campaigns found.[/yellow]")
            return

        table = Table(title="Campaigns")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Client")
        table.add_column("Status")
        table.add_column("Drives")

        for c in campaigns:
            status_color = {
                "draft": "dim",
                "active": "green",
                "completed": "blue",
                "archived": "yellow",
            }.get(c["status"], "white")

            table.add_row(
                c["id"][:8] + "...",
                c["name"],
                c.get("client_name") or "-",
                f"[{status_color}]{c['status']}[/{status_color}]",
                str(c.get("drive_count", 0)),
            )

        console.print(table)

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        sys.exit(1)


# Profile commands
@cli.command("list-profiles")
@require_config
def list_profiles():
    """List all USB profiles."""
    try:
        profiles = client.list_profiles()

        if not profiles:
            console.print("[yellow]No profiles found.[/yellow]")
            return

        table = Table(title="USB Profiles")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Scenario")
        table.add_column("Token Types")

        for p in profiles:
            token_types = ", ".join(p.get("token_config", {}).get("types", []))
            table.add_row(
                p["id"][:8] + "...",
                p["name"],
                p.get("scenario_type", "-"),
                token_types or "-",
            )

        console.print(table)

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        sys.exit(1)


# Drive commands
@cli.command("list-drives")
@click.option("--campaign", "-c", help="Filter by campaign ID")
@click.option(
    "--status",
    "-s",
    type=click.Choice(["created", "prepared", "deployed", "triggered", "recovered"]),
    help="Filter by status",
)
@require_config
def list_drives(campaign: Optional[str], status: Optional[str]):
    """List USB drives."""
    try:
        drives = client.list_drives(campaign_id=campaign, status=status)

        if not drives:
            console.print("[yellow]No drives found.[/yellow]")
            return

        table = Table(title="USB Drives")
        table.add_column("Code", style="cyan")
        table.add_column("Label")
        table.add_column("Status")
        table.add_column("Tokens")
        table.add_column("Triggers")

        for d in drives:
            status_color = {
                "created": "dim",
                "prepared": "blue",
                "deployed": "green",
                "triggered": "red",
                "recovered": "yellow",
            }.get(d["status"], "white")

            table.add_row(
                d["unique_code"],
                d.get("label") or "-",
                f"[{status_color}]{d['status']}[/{status_color}]",
                str(d.get("token_count", 0)),
                str(d.get("trigger_count", 0)),
            )

        console.print(table)

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        sys.exit(1)


@cli.command("prepare")
@click.option("--campaign", "-c", help="Campaign ID (or use default)")
@click.option("--profile", "-p", help="Profile ID")
@click.option("--label", "-l", help="Drive label")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
@require_config
def prepare_drive(
    campaign: Optional[str],
    profile: Optional[str],
    label: Optional[str],
    interactive: bool,
):
    """Create and prepare a new USB drive."""
    try:
        if interactive:
            # Interactive mode - prompt for all options
            campaigns = client.list_campaigns()
            if not campaigns:
                console.print("[red]No campaigns available.[/red]")
                return

            campaign_choices = [
                questionary.Choice(f"{c['name']} ({c['status']})", value=c["id"])
                for c in campaigns
            ]
            campaign = questionary.select(
                "Select campaign:", choices=campaign_choices
            ).ask()

            if not campaign:
                return

            profiles = client.list_profiles()
            if not profiles:
                console.print("[red]No profiles available.[/red]")
                return

            profile_choices = [
                questionary.Choice(f"{p['name']} ({p['scenario_type']})", value=p["id"])
                for p in profiles
            ]
            profile = questionary.select(
                "Select profile:", choices=profile_choices
            ).ask()

            if not profile:
                return

            label = questionary.text("Drive label (optional):").ask()

        else:
            # Use provided options or defaults
            campaign = campaign or config.default_campaign
            if not campaign:
                console.print(
                    "[red]No campaign specified. Use --campaign or set a default.[/red]"
                )
                return
            if not profile:
                console.print("[red]No profile specified. Use --profile.[/red]")
                return

        # Create the drive
        console.print("[cyan]Creating drive...[/cyan]")
        drive = client.create_drive(campaign, profile, label or None)
        console.print(f"[green]Drive created: {drive['unique_code']}[/green]")

        # Prepare the drive (create tokens)
        console.print("[cyan]Preparing drive (creating tokens)...[/cyan]")
        prepared = client.prepare_drive(drive["id"])
        console.print("[green]Drive prepared successfully![/green]")

        # Show tokens
        tokens = client.get_drive_tokens(drive["id"])
        if tokens:
            console.print("\n[bold]Tokens created:[/bold]")
            for t in tokens:
                console.print(f"  - {t['token_type']}: {t.get('filename') or 'DNS'}")

        console.print(f"\n[bold]Drive code: {drive['unique_code']}[/bold]")
        console.print(
            f"Download with: [cyan]usb-drop download {drive['id']}[/cyan]"
        )

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        sys.exit(1)


@cli.command("download")
@click.argument("drive_id")
@click.option("--output", "-o", type=click.Path(), help="Output path")
@click.option("--usb", "-u", is_flag=True, help="Write directly to USB drive")
@click.option("--clear", is_flag=True, help="Clear USB before writing")
@require_config
def download_drive(
    drive_id: str, output: Optional[str], usb: bool, clear: bool
):
    """Download drive files as ZIP or write to USB."""
    try:
        if usb:
            # Find and select USB drive
            drives = find_usb_drives()
            if not drives:
                console.print("[red]No USB drives found.[/red]")
                return

            if len(drives) == 1:
                usb_path = drives[0]
                if not questionary.confirm(
                    f"Write to {usb_path}?", default=True
                ).ask():
                    return
            else:
                usb_choices = [
                    questionary.Choice(str(d), value=d) for d in drives
                ]
                usb_path = questionary.select(
                    "Select USB drive:", choices=usb_choices
                ).ask()

            if not usb_path:
                return

            # Download and extract
            download_and_extract(client, drive_id, usb_path, clear)

            # Verify contents
            summary = verify_usb_contents(usb_path)
            console.print(
                f"\n[green]Written {summary['total_files']} files "
                f"({summary['total_size_mb']} MB)[/green]"
            )

        else:
            # Download to file
            output_path = Path(output) if output else Path(f"drive-{drive_id[:8]}.zip")

            console.print(f"[cyan]Downloading to {output_path}...[/cyan]")
            response = client.download_drive(drive_id)

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            console.print(f"[green]Downloaded: {output_path}[/green]")

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        sys.exit(1)


@cli.command("deploy")
@click.argument("drive_id")
@click.option("--lat", type=float, help="Latitude")
@click.option("--lon", type=float, help="Longitude")
@click.option("--location", "-l", help="Location description")
@click.option("--by", "-b", help="Deployed by (your name)")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
@require_config
def deploy_drive(
    drive_id: str,
    lat: Optional[float],
    lon: Optional[float],
    location: Optional[str],
    by: Optional[str],
    interactive: bool,
):
    """Record drive deployment with GPS coordinates."""
    try:
        if interactive:
            lat_str = questionary.text("Latitude:").ask()
            lon_str = questionary.text("Longitude:").ask()
            lat = float(lat_str) if lat_str else None
            lon = float(lon_str) if lon_str else None
            location = questionary.text("Location description:").ask()
            by = questionary.text("Deployed by:").ask()

        if lat is None or lon is None:
            console.print("[red]Coordinates required. Use --lat and --lon.[/red]")
            return

        result = client.deploy_drive(
            drive_id,
            latitude=lat,
            longitude=lon,
            location_description=location,
            deployed_by=by,
        )

        console.print("[green]Deployment recorded![/green]")
        console.print(f"  Location: {lat:.6f}, {lon:.6f}")
        if location:
            console.print(f"  Description: {location}")

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        sys.exit(1)


@cli.command("alerts")
@click.option("--hours", "-h", default=24, help="Hours to look back (default: 24)")
@require_config
def show_alerts(hours: int):
    """Show recent trigger alerts."""
    try:
        alerts = client.list_alerts(hours=hours)

        if not alerts:
            console.print(f"[yellow]No alerts in the last {hours} hours.[/yellow]")
            return

        table = Table(title=f"Alerts (Last {hours} hours)")
        table.add_column("Time", style="dim")
        table.add_column("Drive", style="cyan")
        table.add_column("Token")
        table.add_column("IP")
        table.add_column("Location")

        for a in alerts:
            from datetime import datetime

            triggered = datetime.fromisoformat(
                a["triggered_at"].replace("Z", "+00:00")
            )
            time_str = triggered.strftime("%m/%d %H:%M")

            location = ""
            if a.get("geo_city") or a.get("geo_country"):
                location = f"{a.get('geo_city', '')}"
                if a.get("geo_country"):
                    location += f", {a['geo_country']}" if location else a["geo_country"]

            table.add_row(
                time_str,
                a["drive_code"],
                a["token_type"],
                a.get("source_ip") or "Unknown",
                location or "-",
            )

        console.print(table)

        # Show summary
        stats = client.get_alert_stats()
        console.print(f"\n[bold]Total triggers:[/bold] {stats.get('total', 0)}")
        console.print(f"[bold]Today:[/bold] {stats.get('today', 0)}")

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        sys.exit(1)


@cli.command("status")
@click.argument("code")
@require_config
def drive_status(code: str):
    """Get status of a drive by its unique code."""
    try:
        drive = client.get_drive_by_code(code)

        console.print(f"\n[bold]Drive: {drive['unique_code']}[/bold]")
        console.print(f"  Label: {drive.get('label') or '-'}")
        console.print(f"  Status: {drive['status']}")
        console.print(f"  Created: {drive.get('created_at', '-')}")

        if drive.get("deployed_at"):
            console.print(f"  Deployed: {drive['deployed_at']}")

        # Get tokens and triggers
        tokens = client.get_drive_tokens(drive["id"])
        trigger_count = sum(t.get("trigger_count", 0) for t in tokens)

        console.print(f"\n  Tokens: {len(tokens)}")
        console.print(f"  Triggers: {trigger_count}")

        if tokens:
            console.print("\n  [bold]Token Details:[/bold]")
            for t in tokens:
                triggers = t.get("trigger_count", 0)
                status = "[red]TRIGGERED[/red]" if triggers > 0 else "[dim]waiting[/dim]"
                console.print(
                    f"    - {t['token_type']}: {t.get('filename') or 'DNS'} - {status}"
                )

    except APIError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
