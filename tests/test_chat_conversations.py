import asyncio
import pytest
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from app.core.llm import generate_characters_from_theme
from app.api.routes.chat import (
    list_conversations,
    get_conversation_details,
    delete_conversation,
    start_character_session,
    generate_character_response,
    Message,
    MessageRole,
    get_conversation,
    CharacterContext,
)

console = Console()


class ChatTestRunner:
    """Test runner for therapeutic chat conversations with pretty output"""
    
    def __init__(self):
        self.conversations = []
        self.characters = []
        self.test_results = []
    
    async def generate_test_characters(self, theme: str = "urban coffee shop"):
        """Generate characters for testing"""
        with console.status("[bold green]Generating test characters...", spinner="dots"):
            try:
                response = await generate_characters_from_theme(theme)
                self.characters = response.characters
                console.print(f"[green]✅ Generated {len(self.characters)} characters[/green]")
                return response
            except Exception as e:
                console.print(f"[red]❌ Failed to generate characters: {str(e)}[/red]")
                raise
    
    def display_characters(self):
        """Display generated characters in a pretty table"""
        table = Table(title="Generated Characters", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Mental State", style="yellow")
        table.add_column("Outfit", style="blue")
        table.add_column("Problems", style="red", width=40)
        
        for char in self.characters:
            table.add_row(
                char.name,
                char.mental_state,
                f"{char.shirt.value} + {char.pants.value}",
                char.problems[:37] + "..." if len(char.problems) > 40 else char.problems
            )
        
        console.print(table)
    
    def get_character_context(self, character_index: int) -> CharacterContext:
        """Get character context for API calls"""
        if character_index >= len(self.characters):
            raise ValueError(f"Character index {character_index} out of range")
        
        char = self.characters[character_index]
        return CharacterContext(
            name=char.name,
            mental_state=char.mental_state,
            problems=char.problems,
            background=char.background,
            interaction_warning=char.interaction_warning
        )
    
    async def interactive_therapy_session(self, character_index: int = 0):
        """Interactive therapy session where client speaks first"""
        if not self.characters:
            raise ValueError("No characters available. Run generate_test_characters first.")
        
        character = self.characters[character_index]
        character_id = f"char_{character_index}"
        character_context = self.get_character_context(character_index)
        
        console.print(Panel(f"[bold cyan]🧠 Interactive Therapy Session with {character.name}[/bold cyan]"))
        console.print(f"[dim]Mental State:[/dim] {character.mental_state}")
        console.print(f"[dim]Problems:[/dim] {character.problems[:100]}...")
        
        # Start session with character speaking first
        conversation_id, initial_message = await start_character_session(character_id, character_context)
        self.conversations.append(conversation_id)
        
        # Track emotional health (client-side simulation)
        emotional_health = 50  # Start at neutral (0-100 scale)
        
        console.print(f"[green]{character.name}:[/green] {initial_message}")
        console.print(f"[yellow]Emotional Health: {emotional_health}/100[/yellow]")
        console.print("[dim]Type 'quit' to end session, 'help' for tips[/dim]\n")
        
        session_ended = False
        message_count = 1  # Start at 1 since character spoke first
        
        while not session_ended:
            # Get therapist input
            therapist_message = Prompt.ask("[blue]Therapist[/blue]")
            
            if therapist_message.lower() == 'quit':
                console.print("[yellow]Session ended by therapist[/yellow]")
                break
            elif therapist_message.lower() == 'help':
                console.print(Panel(
                    "[bold]Therapy Tips:[/bold]\n"
                    "• Use empathy: 'I hear how difficult this is for you'\n"
                    "• Validate feelings: 'Your feelings are completely valid'\n"
                    "• Ask open questions: 'What would be most helpful right now?'\n"
                    "• Avoid judgment: Don't tell them what to do\n"
                    "• Be present: Focus on their experience",
                    title="Therapy Guidelines"
                ))
                continue
            elif not therapist_message.strip():
                continue
            
            # Generate character response
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Character is responding...", total=None)
                
                try:
                    # Get the conversation and add the therapist message
                    conversation = None
                    for conv_id in self.conversations:
                        if conv_id == conversation_id:
                            conversation = get_conversation(conv_id)
                            break
                    
                    if not conversation:
                        raise ValueError("Conversation not found")
                    
                    # Add therapist message
                    therapist_message = Message(
                        role=MessageRole.USER,
                        content=therapist_message
                    )
                    conversation.messages.append(therapist_message)
                    
                    # Generate character response with actual character context
                    character_response = await generate_character_response(
                        messages=conversation.messages,
                        character_context=character_context
                    )
                    
                    # Add character response to conversation
                    character_msg = Message(
                        role=MessageRole.ASSISTANT,
                        content=character_response.comment
                    )
                    conversation.messages.append(character_msg)
                    
                    progress.update(task, description="✅ Response generated")
                    
                    # Update emotional health
                    emotional_health += character_response.emotional_change
                    emotional_health = max(0, min(100, emotional_health))
                    message_count += 1
                    
                except Exception as e:
                    progress.update(task, description="❌ Error generating response")
                    console.print(f"[red]Error: {str(e)}[/red]")
                    continue
            
            # Display response and health
            console.print(f"[green]{character.name}:[/green] {character_response.comment}")
            
            # Show emotional change
            change_color = "green" if character_response.emotional_change >= 0 else "red"
            change_symbol = "+" if character_response.emotional_change >= 0 else ""
            console.print(f"[{change_color}]Emotional Health: {emotional_health}/100 (Change: {change_symbol}{character_response.emotional_change})[/{change_color}]")
            
            # Check session end conditions
            if character_response.satisfied or character_response.enraged:
                if character_response.satisfied:
                    console.print(Panel.fit(
                        "[bold green]🎉 Character is satisfied! Therapy successful![/bold green]",
                        border_style="green"
                    ))
                elif character_response.enraged:
                    console.print(Panel.fit(
                        "[bold red]💥 Character is enraged! Therapy failed![/bold red]",
                        border_style="red"
                    ))
                session_ended = True
            elif emotional_health >= 90:
                console.print(Panel.fit(
                    "[bold green]🌟 Character is feeling much better![/bold green]",
                    border_style="green"
                ))
                session_ended = True
            elif emotional_health <= 10:
                console.print(Panel.fit(
                    "[bold red]💀 Character is in crisis![/bold red]",
                    border_style="red"
                ))
                session_ended = True
            
            console.print()  # Empty line for spacing
        
        # Session summary
        console.print(Panel(
            f"[bold]Session Summary:[/bold]\n"
            f"Final Emotional Health: {emotional_health}/100\n"
            f"Messages Exchanged: {message_count}\n"
            f"Outcome: {'Success' if emotional_health > 50 else 'Needs Improvement'}",
            title="Therapy Session Complete"
        ))
        
        return True
    
    async def test_fast_therapy_session(self, character_index: int = 0):
        """Test a fast-paced therapy session with a character"""
        if not self.characters:
            raise ValueError("No characters available. Run generate_test_characters first.")
        
        character = self.characters[character_index]
        character_id = f"char_{character_index}"
        character_context = self.get_character_context(character_index)
        
        console.print(Panel(f"[bold cyan]⚡ Fast Therapy Session with {character.name}[/bold cyan]"))
        console.print(f"[dim]Mental State:[/dim] {character.mental_state}")
        console.print(f"[dim]Problems:[/dim] {character.problems[:100]}...")
        
        # Start session with character speaking first
        conversation_id, initial_message = await start_character_session(character_id, character_context)
        self.conversations.append(conversation_id)
        
        # Track emotional health (client-side simulation)
        emotional_health = 50  # Start at neutral (0-100 scale)
        
        console.print(f"[green]{character.name}:[/green] {initial_message}")
        console.print(f"[yellow]Emotional Health: {emotional_health}/100[/yellow]")
        
        # Test with a single therapy message
        therapy_message = "Hello, I'm here to help. What brings you in today?"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Testing therapy response...", total=None)
            
            try:
                # Create a custom request with character context
                
                # Get the conversation and add the therapist message
                conversation = None
                for conv_id in self.conversations:
                    if conv_id == conversation_id:
                        conversation = get_conversation(conv_id)
                        break
                
                if not conversation:
                    raise ValueError("Conversation not found")
                
                # Add therapist message
                therapist_message = Message(
                    role=MessageRole.USER,
                    content=therapy_message
                )
                conversation.messages.append(therapist_message)
                
                # Generate character response with actual character context
                character_response = await generate_character_response(
                    messages=conversation.messages,
                    character_context=character_context
                )
                
                # Add character response to conversation
                character_msg = Message(
                    role=MessageRole.ASSISTANT,
                    content=character_response.comment
                )
                conversation.messages.append(character_msg)
                
                progress.update(task, description="✅ Response generated")
                
                # Update emotional health
                emotional_health += character_response.emotional_change
                emotional_health = max(0, min(100, emotional_health))
                
                console.print(f"[blue]Therapist:[/blue] {therapy_message}")
                console.print(f"[green]Client:[/green] {character_response.comment}")
                console.print(f"[yellow]Emotional Health: {emotional_health}/100 (Change: {character_response.emotional_change:+d})[/yellow]")
                
                if character_response.satisfied or character_response.enraged:
                    console.print(f"[bold red]Session ended: {'Satisfied' if character_response.satisfied else 'Enraged'}[/bold red]")
                    return True
                
            except Exception as e:
                progress.update(task, description="❌ Failed to generate response")
                console.print(f"[red]Error: {str(e)}[/red]")
                return False
        
        # Session outcome
        if emotional_health >= 85:
            console.print(f"[bold green]🌟 Therapy successful! Final Health: {emotional_health}/100[/bold green]")
        elif emotional_health <= 15:
            console.print(f"[bold red]💀 Therapy failed! Final Health: {emotional_health}/100[/bold red]")
        else:
            console.print(f"[bold yellow]⚠️ Therapy needs improvement. Final Health: {emotional_health}/100[/bold yellow]")
        
        return True
    
    async def test_conversation_management(self):
        """Test conversation management functions"""
        console.print(Panel("[bold blue]Testing Therapy Session Management[/bold blue]"))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Listing therapy sessions...", total=None)
            
            try:
                conversations = await list_conversations()
                progress.update(task, description="✅ Therapy sessions listed")
                
                table = Table(title="All Therapy Sessions", show_header=True, header_style="bold green")
                table.add_column("ID", style="cyan", width=36)
                table.add_column("Title", style="yellow")
                table.add_column("Messages", style="blue")
                table.add_column("Character ID", style="magenta")
                
                for conv in conversations["conversations"]:
                    table.add_row(
                        conv["id"][:8] + "...",
                        conv["title"] or "Untitled",
                        str(conv["message_count"]),
                        conv.get("character_id", "None")
                    )
                
                console.print(table)
                
            except Exception as e:
                progress.update(task, description="❌ Failed to list therapy sessions")
                console.print(f"[red]Error: {str(e)}[/red]")
                return False
        
        if self.conversations:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Getting therapy session details...", total=None)
                
                try:
                    details = await get_conversation_details(self.conversations[0])
                    progress.update(task, description="✅ Therapy session details retrieved")
                    
                    console.print(Panel(
                        f"[bold]Therapy Session Details:[/bold]\n"
                        f"Title: {details['title']}\n"
                        f"Messages: {len(details['messages'])}\n"
                        f"Character ID: {details.get('character_id', 'None')}",
                        title="Session Info"
                    ))
                    
                except Exception as e:
                    progress.update(task, description="❌ Failed to get session details")
                    console.print(f"[red]Error: {str(e)}[/red]")
                    return False
        
        return True
    
    async def cleanup_conversations(self):
        """Clean up test therapy sessions"""
        console.print(Panel("[bold red]Cleaning up test therapy sessions[/bold red]"))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Deleting therapy sessions...", total=len(self.conversations))
            
            for i, conv_id in enumerate(self.conversations):
                try:
                    await delete_conversation(conv_id)
                    progress.update(task, advance=1, description=f"Deleted session {i+1}/{len(self.conversations)}")
                except Exception as e:
                    console.print(f"[red]Failed to delete session {conv_id}: {str(e)}[/red]")
            
            progress.update(task, description="✅ Cleanup completed")
        
        console.print("[green]All test therapy sessions cleaned up[/green]")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_fast_therapy_system_e2e():
    """End-to-end test of the fast-paced therapy system"""
    
    print("\n\n")
    
    console.print(Panel.fit(
        "[bold magenta]⚡ Fast Therapy System End-to-End Test[/bold magenta]\n"
        "[dim]Testing character generation, fast therapy sessions, and emotional health tracking[/dim]",
        border_style="magenta"
    ))
    
    runner = ChatTestRunner()
    
    try:
        console.print("\n[bold cyan]Step 1: Generating Test Characters[/bold cyan]")
        await runner.generate_test_characters("urban coffee shop")
        runner.display_characters()
        
        console.print("\n[bold cyan]Step 2: Testing Fast Therapy Session[/bold cyan]")
        success = await runner.test_fast_therapy_session(character_index=0)
        assert success, "Fast therapy session test failed"
        
        console.print("\n[bold cyan]Step 3: Testing Session Management[/bold cyan]")
        success = await runner.test_conversation_management()
        assert success, "Session management test failed"
        
        console.print("\n[bold cyan]Step 4: Cleanup[/bold cyan]")
        await runner.cleanup_conversations()
        
        console.print(Panel.fit(
            "[bold green]✅ All Fast Therapy System Tests Passed![/bold green]",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]❌ Fast Therapy System Test Failed: {str(e)}[/bold red]",
            border_style="red"
        ))
        raise


@pytest.mark.asyncio
async def test_interactive_therapy_session():
    """Test interactive therapy session with user input"""
    
    print("\n\n")
    
    console.print(Panel.fit(
        "[bold blue]🧠 Interactive Therapy Session Test[/bold blue]\n"
        "[dim]Test interactive therapy session with character speaking first[/dim]",
        border_style="blue"
    ))
    
    runner = ChatTestRunner()
    
    try:
        await runner.generate_test_characters("busy train station")
        runner.display_characters()
        
        console.print(f"\n[bold yellow]Starting interactive therapy session...[/bold yellow]")
        success = await runner.interactive_therapy_session(character_index=0)
        assert success, "Interactive therapy session test failed"
        
        await runner.cleanup_conversations()
        
        console.print(Panel.fit(
            "[bold green]✅ Interactive Therapy Session Test Passed![/bold green]",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]❌ Interactive Therapy Session Test Failed: {str(e)}[/bold red]",
            border_style="red"
        ))
        raise


@pytest.mark.asyncio
async def test_multiple_character_fast_therapy():
    """Test fast therapy sessions with multiple characters"""
    
    print("\n\n")
    
    console.print(Panel.fit(
        "[bold blue]⚡ Multiple Character Fast Therapy Test[/bold blue]",
        border_style="blue"
    ))
    
    runner = ChatTestRunner()
    
    try:
        await runner.generate_test_characters("busy train station")
        runner.display_characters()
        
        for i in range(min(2, len(runner.characters))):
            console.print(f"\n[bold yellow]Testing Fast Therapy with Character {i+1}: {runner.characters[i].name}[/bold yellow]")
            success = await runner.test_fast_therapy_session(character_index=i)
            assert success, f"Fast therapy test failed for character {i+1}"
        
        await runner.cleanup_conversations()
        
        console.print(Panel.fit(
            "[bold green]✅ Multiple Character Fast Therapy Test Passed![/bold green]",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]❌ Multiple Character Fast Therapy Test Failed: {str(e)}[/bold red]",
            border_style="red"
        ))
        raise


async def main():
    """Run all fast therapy tests with pretty output"""

    print("\n\n")
    
    console.print(Panel.fit(
        "[bold magenta]⚡ Fast Therapy System Test Suite[/bold magenta]\n"
        "[dim]Testing character generation and fast therapeutic interactions (1-minute sessions)[/dim]",
        border_style="magenta"
    ))
    
    try:
        await test_fast_therapy_system_e2e()
        await test_interactive_therapy_session()
        await test_multiple_character_fast_therapy()
        
        console.print(Panel.fit(
            "[bold green]🎉 All Fast Therapy Tests Completed Successfully![/bold green]",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]💥 Test Suite Failed: {str(e)}[/bold red]",
            border_style="red"
        ))
        raise


if __name__ == "__main__":
    asyncio.run(main()) 