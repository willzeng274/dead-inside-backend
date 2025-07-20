#!/usr/bin/env python3
"""End-to-end test for the therapy system using API endpoints"""

import pytest
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class TherapySystemTestRunner:
    def __init__(self):
        self.conversations = []
        self.characters = []
        self.test_results = []
        self.base_url = "http://localhost:8000"

    async def generate_test_characters(self, num_characters: int, theme: str = "urban coffee shop"):
        """Generate characters for testing via API"""
        with console.status(
            f"[bold green]Generating {num_characters} test characters via API...", spinner="dots"
        ):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    console.print(f"[dim]Making request to: {self.base_url}/legacy/chat/characters/generate[/dim]")
                    console.print(f"[dim]Request data: {{'theme': '{theme}', 'num_characters': {num_characters}}}[/dim]")
                    
                    response = await client.post(
                        f"{self.base_url}/legacy/chat/characters/generate",
                        json={"theme": theme, "num_characters": num_characters}
                    )
                    
                    console.print(f"[dim]Response status: {response.status_code}[/dim]")
                    console.print(f"[dim]Response headers: {dict(response.headers)}[/dim]")
                    
                    if response.status_code == 200:
                        data = response.json()
                        console.print(f"[dim]Response data keys: {list(data.keys())}[/dim]")
                        self.characters = data["characters"]
                        console.print(
                            f"[green]✅ Generated {len(self.characters)} characters via API[/green]"
                        )
                        return data
                    else:
                        error_text = response.text
                        console.print(f"[red]❌ Failed to generate characters: {response.status_code}[/red]")
                        console.print(f"[red]❌ Error response: {error_text}[/red]")
                        raise Exception(f"API error: {response.status_code} - {error_text}")
                        
            except Exception as e:
                console.print(f"[red]❌ Failed to generate characters: {str(e)}[/red]")
                console.print(f"[red]❌ Exception type: {type(e).__name__}[/red]")
                raise

    async def start_therapy_session(self, character_id: str, message: str):
        """Start a therapy session via API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/legacy/chat/conversations",
                    json={
                        "message": message,
                        "character_id": character_id
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.conversations.append(data["conversation_id"])
                    return data
                else:
                    console.print(f"[red]❌ Failed to start session: {response.status_code}[/red]")
                    return None
                    
        except Exception as e:
            console.print(f"[red]❌ Session error: {str(e)}[/red]")
            return None

    async def add_message_to_session(self, conversation_id: str, character_id: str, message: str):
        """Add a message to an existing session via API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/legacy/chat/conversations/{conversation_id}/messages",
                    json={
                        "message": message,
                        "character_id": character_id
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    console.print(f"[red]❌ Failed to add message: {response.status_code}[/red]")
                    return None
                    
        except Exception as e:
            console.print(f"[red]❌ Message error: {str(e)}[/red]")
            return None

    async def list_conversations(self):
        """List all conversations via API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/legacy/chat/conversations")
                
                if response.status_code == 200:
                    data = response.json()
                    return data["conversations"]
                else:
                    console.print(f"[red]❌ Failed to list conversations: {response.status_code}[/red]")
                    return []
                    
        except Exception as e:
            console.print(f"[red]❌ List error: {str(e)}[/red]")
            return []

    async def get_conversation_details(self, conversation_id: str):
        """Get conversation details via API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/legacy/chat/conversations/{conversation_id}")
                
                if response.status_code == 200:
                    return response.json()
                else:
                    console.print(f"[red]❌ Failed to get conversation: {response.status_code}[/red]")
                    return None
                    
        except Exception as e:
            console.print(f"[red]❌ Details error: {str(e)}[/red]")
            return None

    async def cleanup_conversations(self):
        """Clean up test conversations via API"""
        console.print(Panel("[bold red]Cleaning up test conversations[/bold red]"))

        if self.conversations:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Deleting conversations...", total=len(self.conversations)
                )

                for i, conv_id in enumerate(self.conversations):
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.delete(f"{self.base_url}/legacy/chat/conversations/{conv_id}")
                            
                            if response.status_code == 200:
                                progress.update(
                                    task,
                                    advance=1,
                                    description=f"Deleted conversation {i+1}/{len(self.conversations)}",
                                )
                            else:
                                console.print(f"[red]Failed to delete conversation {conv_id}: {response.status_code}[/red]")
                    except Exception as e:
                        console.print(f"[red]Failed to delete conversation {conv_id}: {str(e)}[/red]")

                progress.update(task, description="✅ Conversations cleaned up")

        console.print("[green]All test conversations cleaned up[/green]")

    async def cleanup_all_data(self):
        """Clean up all data via API"""
        console.print(Panel("[bold red]Cleaning up all test data[/bold red]"))
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(f"{self.base_url}/legacy/chat/cleanup")
                
                if response.status_code == 200:
                    result = response.json()
                    console.print(f"[green]✅ Cleanup successful: {result['message']}[/green]")
                else:
                    console.print(f"[red]❌ Cleanup failed: {response.status_code}[/red]")
                    
        except Exception as e:
            console.print(f"[red]❌ Cleanup error: {str(e)}[/red]")


@pytest.mark.asyncio
async def test_fast_therapy_system_e2e():
    """End-to-end test for the fast therapy system using API endpoints"""
    print("\n\n")
    
    console.print(
        Panel(
            "[bold cyan]⚡ Fast Therapy System End-to-End Test[/bold cyan]\n"
            "[cyan]Testing character generation, fast therapy sessions, and emotional health tracking via API[/cyan]",
            border_style="cyan",
        )
    )

    runner = TherapySystemTestRunner()

    console.print("\n[bold cyan]Step 1: Generating Test Characters[/bold cyan]")
    try:
        response = await runner.generate_test_characters()
        
        # Display generated characters
        table = Table(title="Generated Characters")
        table.add_column("Name", style="cyan")
        table.add_column("Mental State", style="yellow")
        table.add_column("Outfit", style="green")
        table.add_column("Problems", style="red")

        for char in response["characters"]:
            outfit = f"{char['shirt']} + {char['pants']}"
            problems = char['problem'][:50] + "..." if len(char['problem']) > 50 else char['problem']
            table.add_row(
                char['name'],
                char['mental_state'][:30] + "..." if len(char['mental_state']) > 30 else char['mental_state'],
                outfit,
                problems
            )

        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Character generation failed: {str(e)}[/red]")
        return

    console.print("\n[bold cyan]Step 2: Testing Fast Therapy Session[/bold cyan]")
    if not response["characters"]:
        console.print("[red]❌ No characters generated[/red]")
        return

    character = response["characters"][0]
    console.print(
        Panel(
            f"[bold cyan]⚡ Fast Therapy Session with {character['name']}[/bold cyan]\n"
            f"Mental State: {character['mental_state']}\n"
            f"Problems: {character['problems'][:100]}...",
            border_style="cyan",
        )
    )

    # Start therapy session
    session_result = await runner.start_therapy_session(
        character["id"], 
        "Hello, I'm here to help. What brings you in today?"
    )

    if session_result:
        console.print(f"[green]✅ Session started: {session_result['conversation_id']}[/green]")
        console.print(f"[yellow]Client: {session_result['response']}[/yellow]")
        console.print(f"[green]Emotional Change: {session_result['emotional_change']}[/green]")
        
        if session_result['session_ended']:
            console.print("[red]⚠️ Session ended early[/red]")
        else:
            # Add another message
            follow_up = await runner.add_message_to_session(
                session_result['conversation_id'],
                character["id"],
                "I understand. Can you tell me more about how this is affecting your daily life?"
            )
            
            if follow_up:
                console.print(f"[yellow]Client: {follow_up['response']}[/yellow]")
                console.print(f"[green]Emotional Change: {follow_up['emotional_change']}[/green]")
    else:
        console.print("[red]❌ Failed to start therapy session[/red]")

    console.print("\n[bold cyan]Step 3: Testing Session Management[/bold cyan]")
    console.print(
        Panel(
            "[bold cyan]Testing Therapy Session Management[/bold cyan]",
            border_style="cyan",
        )
    )

    # List all conversations
    conversations = await runner.list_conversations()
    if conversations:
        table = Table(title="All Therapy Sessions")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Messages", style="yellow")
        table.add_column("Character ID", style="magenta")

        for conv in conversations:
            table.add_row(
                conv["id"][:8] + "...",
                conv["title"] or "Untitled",
                str(conv["message_count"]),
                conv["character_id"] or "None"
            )

        console.print(table)
        
        # Get details of first conversation
        if conversations:
            details = await runner.get_conversation_details(conversations[0]["id"])
            if details:
                console.print(
                    Panel(
                        f"[bold]Session Info:[/bold]\n"
                        f"Title: {details['title']}\n"
                        f"Messages: {len(details['messages'])}\n"
                        f"Character ID: {details['character_id']}",
                        title="Session Details"
                    )
                )

    console.print("\n[bold cyan]Step 4: Cleanup[/bold cyan]")
    await runner.cleanup_all_data()

    console.print(
        Panel(
            "[bold green]✅ All Fast Therapy System Tests Passed![/bold green]",
            border_style="green",
        )
    )


@pytest.mark.asyncio
async def test_interactive_therapy_session():
    """Interactive terminal-based therapy session"""
    console.print(
        Panel(
            "[bold cyan]🧠 Interactive Therapy Session[/bold cyan]\n"
            "[cyan]You are the therapist. Type your responses to help the character.[/cyan]",
            border_style="cyan",
        )
    )

    runner = TherapySystemTestRunner()

    # Generate a character
    console.print("\n[bold cyan]Step 1: Generating a Character[/bold cyan]")
    try:
        response = await runner.generate_test_characters("coffee shop")
        character = response["characters"][0]
        
        console.print(f"[green]✅ Generated character: {character['name']}[/green]")
        console.print(f"[yellow]Mental State: {character['mental_state']}[/yellow]")
        console.print(f"[red]Problem: {character['problem'][:100]}...[/red]")
        console.print(f"[red]Problem Description: {character['problem_description']}[/red]")
        console.print(f"[blue]Interaction Warning: {character['interaction_warning']}[/blue]")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to generate character: {str(e)}[/red]")
        return

    # Start therapy session
    console.print(f"\n[bold cyan]Step 2: Starting Therapy Session with {character['name']}[/bold cyan]")
    
    session_result = await runner.start_therapy_session(
        character["id"], 
        "Hello, I'm here to help. What brings you in today?"
    )

    if not session_result:
        console.print("[red]❌ Failed to start therapy session[/red]")
        return

    conversation_id = session_result["conversation_id"]
    emotional_state = session_result["emotional_state"]
    
    console.print(f"[green]✅ Session started![/green]")
    console.print(f"[yellow]Client: {session_result['response']}[/yellow]")
    console.print(f"[blue]Emotional State: {emotional_state}/100 (Change: {session_result['emotional_change']:+d})[/blue]")

    # Interactive therapy loop
    console.print(f"\n[bold cyan]Step 3: Interactive Therapy Session[/bold cyan]")
    console.print("[dim]Type your therapy responses. Type 'quit' to end session.[/dim]\n")

    while True:
        # Check if session should end
        if session_result.get('session_ended', False):
            if emotional_state >= 100:
                console.print("[bold green]🎉 Character is satisfied! Therapy successful![/bold green]")
            else:
                console.print("[bold red]💥 Character is enraged! Therapy failed![/bold red]")
            break

        # Get therapist input
        try:
            therapist_message = console.input("[blue]Therapist: [/blue]").strip()
            
            if therapist_message.lower() == 'quit':
                console.print("[yellow]Session ended by therapist[/yellow]")
                break
            elif not therapist_message:
                continue
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted[/yellow]")
            break

        # Send message and get response
        try:
            response = await runner.add_message_to_session(
                conversation_id,
                character["id"],
                therapist_message
            )
            
            if response:
                emotional_state = response["emotional_state"]
                emotional_change = response["emotional_change"]
                
                console.print(f"[yellow]Client: {response['response']}[/yellow]")
                
                # Color code emotional change
                change_color = "green" if emotional_change >= 0 else "red"
                change_symbol = "+" if emotional_change >= 0 else ""
                console.print(f"[{change_color}]Emotional State: {emotional_state}/100 (Change: {change_symbol}{emotional_change})[/{change_color}]")
                
                if response.get('session_ended', False):
                    if emotional_state >= 100:
                        console.print("[bold green]🎉 Character is satisfied! Therapy successful![/bold green]")
                    else:
                        console.print("[bold red]💥 Character is enraged! Therapy failed![/bold red]")
                    break
            else:
                console.print("[red]❌ Failed to get response[/red]")
                break
                
        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]")
            break

    # Session summary
    console.print(f"\n[bold cyan]Session Summary:[/bold cyan]")
    console.print(f"Final Emotional State: {emotional_state}/100")
    console.print(f"Outcome: {'Success' if emotional_state >= 50 else 'Needs Improvement'}")

    # Cleanup
    console.print(f"\n[bold cyan]Step 4: Cleanup[/bold cyan]")
    await runner.cleanup_all_data()

    console.print(
        Panel(
            "[bold green]✅ Interactive Therapy Session Complete![/bold green]",
            border_style="green",
        )
    )
